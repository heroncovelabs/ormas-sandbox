"""LockCore lease manager, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys

_DIGITS = frozenset("0123456789")
_ALNUM = frozenset("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _is_id(tok: str) -> bool:
    """Client and resource ids: 1-8 ASCII alphanumerics."""
    return 1 <= len(tok) <= 8 and all(c in _ALNUM for c in tok)


def _is_ttl_token(tok: str) -> bool:
    """TTL token: 1-3 ASCII digits."""
    return 1 <= len(tok) <= 3 and all(c in _DIGITS for c in tok)


class Resource:
    __slots__ = (
        "name", "holder", "expiry", "orig", "queue", "expired_holder", "reclaim_until"
    )

    def __init__(self, name: str):
        self.name = name
        self.holder: str | None = None
        self.expiry = 0
        self.orig = 0
        self.queue: list[tuple[str, int]] = []  # (client, ttl)
        self.expired_holder: str | None = None
        self.reclaim_until = 0


class Engine:
    def __init__(self, out=None):
        self.resources: list[Resource] = []
        self.by_name: dict[str, Resource] = {}  # keyed by case-folded name
        self.clients: dict[str, str] = {}  # case-folded id -> first spelling seen
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

    def _client_name(self, cid: str) -> str:
        """Canonical spelling of a client id without registering it."""
        return self.clients.get(cid.lower(), cid)

    def _intern_client(self, cid: str) -> str:
        """Canonical spelling of a client id, registering it on first sight."""
        return self.clients.setdefault(cid.lower(), cid)

    def _grant(self, r: Resource, client: str, ttl: int) -> None:
        r.holder = client
        # Long resource names use the legacy engine's capped lease duration.
        r.orig = min(ttl, 100) if len(r.name) >= 6 else ttl
        r.expiry = self.now + r.orig
        if r.expired_holder == client:
            r.expired_holder = None
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
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        cid = parts[1] if len(parts) > 1 else ""
        cli_ok = _is_id(cid)
        echo = cid if cli_ok else "????????"
        rid = parts[2] if len(parts) > 2 else ""

        if kind == "A":
            if len(parts) < 4 or not cli_ok or not _is_id(rid):
                self._reject(echo, "FMT")
                return
            ttok = parts[3]
            if not _is_ttl_token(ttok):
                self._reject(cid, "TTL")
                return
            ttl = int(ttok)
            if not 1 <= ttl <= 999:
                self._reject(cid, "TTL")
                return
            client = self._intern_client(cid)
            r = self.by_name.get(rid.lower())
            if r is not None and (
                r.holder == client or any(w == client for w, _ in r.queue)
            ):
                self._reject(client, "STATE")
                return
            if r is None:
                r = Resource(rid)
                self.resources.append(r)
                self.by_name[rid.lower()] = r
            if r.holder is None:
                self._grant(r, client, ttl)
            else:
                # A recent expiry earns a place at the front on re-entry.
                if r.expired_holder == client and self.now <= r.reclaim_until:
                    r.queue.insert(0, (client, ttl))
                else:
                    r.queue.append((client, ttl))
                self._emit(f"Q {len(r.queue)}")
            self.c_acq += 1
            self.now += 1
            return

        if kind == "R":
            if len(parts) < 3 or not cli_ok or not _is_id(rid):
                self._reject(echo, "FMT")
                return
            client = self._client_name(cid)
            r = self.by_name.get(rid.lower())
            if r is None or r.holder != client or r.expiry <= self.now:
                self._reject(client, "STATE")
                return
            # Each successful renewal wears one tick off this grant's TTL.
            r.orig = max(1, r.orig - 1)
            r.expiry = self.now + r.orig
            self._emit(f"OK {self._holds_of(client)}")
            self.c_ren += 1
            self.now += 1
            return

        if kind == "E":
            released = 0
            for r in self.resources:
                if r.holder is not None and r.expiry <= self.now:
                    r.expired_holder = r.holder
                    r.reclaim_until = self.now + 10
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
            client = self._intern_client(cid)
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
