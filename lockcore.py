"""LockCore lease manager, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys


def _valid_id(value: str) -> bool:
    return (
        1 <= len(value) <= 8
        and value.isascii()
        and value.isalnum()
    )


class Resource:
    __slots__ = (
        "name", "holder", "expiry", "orig", "renewals", "queue",
        "expired_client", "expired_at",
    )

    def __init__(self, name: str):
        self.name = name
        self.holder: str | None = None
        self.expiry = 0
        self.orig = 0
        self.renewals = 0
        # Queue entries are (canonical client, ttl, grace priority).
        self.queue: list[tuple[str, int, bool]] = []
        self.expired_client: str | None = None
        self.expired_at = 0


class Engine:
    def __init__(self, out=None):
        self.resources: list[Resource] = []
        self.by_name: dict[str, Resource] = {}
        self.client_names: dict[str, str] = {}
        self.now = 0
        self.c_acq = 0
        self.c_ren = 0
        self.c_swp = 0
        self.c_rej = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _client_key(self, client: str) -> str:
        key = client.lower()
        self.client_names.setdefault(key, client)
        return key

    def _reject(self, echo: str, code: str) -> None:
        self._emit(f"N {echo} {code}")
        self.c_rej += 1

    def _holds_of(self, client: str) -> int:
        return sum(1 for r in self.resources if r.holder == client)

    def _grant(self, r: Resource, client: str, ttl: int) -> None:
        r.holder = client
        # The old fixed-size resource slot capped long names' stored TTL.
        r.orig = min(ttl, 100) if len(r.name) >= 6 else ttl
        r.renewals = 0
        r.expiry = self.now + r.orig
        self._emit(f"G {r.name} {self.client_names[client]}")

    def _drain_free(self) -> int:
        granted = 0
        for r in self.resources:  # creation order
            if r.holder is None and r.queue:
                index = next(
                    (i for i, entry in enumerate(r.queue) if entry[2]), 0
                )
                client, ttl, _ = r.queue.pop(index)
                self._grant(r, client, ttl)
                granted += 1
        return granted

    def handle(self, line: str) -> None:
        text = line.rstrip("\r\n")
        if not text:
            return
        parts = re.split(r"[ \t\n\r\f\v]+", text.strip(" \t\n\r\f\v"))
        if parts == [""]:
            parts = []
        kind = parts[0] if parts else ""
        cid = parts[1] if len(parts) > 1 else ""
        cli_ok = _valid_id(cid)
        echo = cid if cli_ok else "????????"
        rid = parts[2] if len(parts) > 2 else ""

        if kind == "A":
            if (
                len(parts) < 4
                or not cli_ok
                or not _valid_id(rid)
            ):
                self._reject(echo, "FMT")
                return
            ttok = parts[3]
            if not (
                ttok.isascii() and ttok.isdigit() and 1 <= len(ttok) <= 3
            ):
                self._reject(cid, "TTL")
                return
            ttl = int(ttok)
            if not 1 <= ttl <= 999:
                self._reject(cid, "TTL")
                return
            client = self._client_key(cid)
            key = client
            rkey = rid.lower()
            r = self.by_name.get(rkey)
            if r is not None and (
                r.holder == key or any(w == key for w, _, _ in r.queue)
            ):
                self._reject(self.client_names[key], "STATE")
                return
            if r is None:
                r = Resource(rid)
                self.resources.append(r)
                self.by_name[rkey] = r
            if r.holder is None:
                self._grant(r, client, ttl)
            else:
                priority = (
                    client == r.expired_client
                    and self.now - r.expired_at <= 10
                )
                r.queue.append((client, ttl, priority))
                self._emit(f"Q {len(r.queue)}")
            self.c_acq += 1
            self.now += 1
            return

        if kind == "R":
            if (
                len(parts) < 3
                or not cli_ok
                or not _valid_id(rid)
            ):
                self._reject(echo, "FMT")
                return
            key = cid.lower()
            r = self.by_name.get(rid.lower())
            if r is None or r.holder != key or r.expiry <= self.now:
                self._reject(self.client_names.get(key, cid), "STATE")
                return
            client = self._client_key(cid)
            r.renewals += 1
            r.expiry = self.now + r.orig - r.renewals
            self._emit(f"OK {self._holds_of(client)}")
            self.c_ren += 1
            self.now += 1
            return

        if kind == "E":
            released = 0
            for r in self.resources:
                if r.holder is not None and r.expiry <= self.now:
                    r.expired_client = r.holder
                    r.expired_at = self.now
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
            client = self._client_key(cid)
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
