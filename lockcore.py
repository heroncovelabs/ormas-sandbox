"""LockCore lease manager, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys


def _valid_id(value: str) -> bool:
    return 1 <= len(value) <= 8 and all(
        "0" <= c <= "9" or "A" <= c <= "Z" or "a" <= c <= "z"
        for c in value
    )


class Resource:
    __slots__ = (
        "name",
        "holder",
        "expiry",
        "orig",
        "queue",
        "grace_client",
        "grace_until",
    )

    def __init__(self, name: str):
        self.name = name
        self.holder: str | None = None
        self.expiry = 0
        self.orig = 0
        self.queue: list[tuple[str, int]] = []  # (client, ttl)
        self.grace_client: str | None = None
        self.grace_until = -1


class Engine:
    def __init__(self, out=None):
        self.resources: list[Resource] = []
        self.by_name: dict[str, Resource] = {}
        self.clients: dict[str, str] = {}
        self.now = 0
        self.c_acq = 0
        self.c_ren = 0
        self.c_swp = 0
        self.c_rej = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, echo: str, code: str) -> None:
        self._emit(f"N {echo} {code}")
        self.c_rej += 1

    def _holds_of(self, client: str) -> int:
        return sum(1 for r in self.resources if r.holder == client)

    def _grant(self, r: Resource, client: str, ttl: int) -> None:
        r.holder = client
        # The legacy fixed-size resource path caps long-name leases.
        r.orig = min(ttl, 100) if len(r.name) >= 6 else ttl
        r.expiry = self.now + r.orig
        self._emit(f"G {r.name} {client}")

    def _drain_free(self) -> int:
        granted = 0
        for r in self.resources:  # creation order
            if r.holder is None and r.queue:
                client, ttl = r.queue.pop(0)
                self._grant(r, client, ttl)
                granted += 1
        return granted

    def handle(self, line: str) -> None:
        text = line.rstrip("\r\n")
        if not text:
            return
        parts = text.split()
        if not parts:
            self._reject("????????", "FMT")
            return
        kind = parts[0]
        cid = parts[1] if len(parts) > 1 else ""
        cli_ok = _valid_id(cid)
        echo = cid if cli_ok else "????????"
        rid = parts[2] if len(parts) > 2 else ""
        key = cid.lower()

        if kind == "A":
            if len(parts) < 4 or not cli_ok or not _valid_id(rid):
                self._reject(echo, "FMT")
                return
            ttok = parts[3]
            if not (
                1 <= len(ttok) <= 3
                and all("0" <= c <= "9" for c in ttok)
            ):
                self._reject(cid, "TTL")
                return
            ttl = int(ttok)
            if not 1 <= ttl <= 999:
                self._reject(cid, "TTL")
                return
            r = self.by_name.get(rid.lower())
            if r is not None and (
                (r.holder is not None and r.holder.lower() == key)
                or any(w.lower() == key for w, _ in r.queue)
            ):
                self._reject(self.clients.get(key, cid), "STATE")
                return
            client = self.clients.setdefault(key, cid)
            if r is None:
                r = Resource(rid)
                self.resources.append(r)
                self.by_name[rid.lower()] = r
            if r.holder is None:
                self._grant(r, client, ttl)
            elif (
                r.grace_client is not None
                and r.grace_client.lower() == key
                and self.now <= r.grace_until
            ):
                # Recently expired holders may reclaim at the queue head.
                r.queue.insert(0, (client, ttl))
                self._emit(f"Q {len(r.queue)}")
            else:
                r.queue.append((client, ttl))
                self._emit(f"Q {len(r.queue)}")
            self.c_acq += 1
            self.now += 1
            return

        if kind == "R":
            if len(parts) < 3 or not cli_ok or not _valid_id(rid):
                self._reject(echo, "FMT")
                return
            client = self.clients.get(key, cid)
            r = self.by_name.get(rid.lower())
            if (
                r is None
                or r.holder != client
                or r.expiry <= self.now
            ):
                self._reject(client, "STATE")
                return
            # Each renewal decays the lease's stored ttl by one tick.
            r.orig -= 1
            r.expiry = self.now + r.orig
            self._emit(f"OK {self._holds_of(client)}")
            self.c_ren += 1
            self.now += 1
            return

        if kind == "E":
            released = 0
            for r in self.resources:
                if r.holder is not None and r.expiry <= self.now:
                    r.grace_client = r.holder
                    r.grace_until = self.now + 10
                    r.holder = None
                    released += 1
            granted = self._drain_free()
            self._emit(f"EEND {released} {granted}")
            self.c_swp += 1
            self.now += 1
            return

        if kind == "L":
            if len(parts) < 2 or not cli_ok:
                self._reject(echo, "FMT")
                return
            client = self.clients.setdefault(key, cid)
            released = 0
            for r in self.resources:
                if r.holder == client:
                    r.holder = None
                    released += 1
            self._drain_free()
            self._emit(f"LEND {released}")
            self.now += 1
            return

        self._reject(echo, "FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_acq} {self.c_ren} {self.c_swp} {self.c_rej}")


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
