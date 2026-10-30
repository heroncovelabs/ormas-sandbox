"""LockCore lease manager, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import re
import sys

# The engine splits on ASCII whitespace only.
_TOKEN = re.compile(r"[^ \t\n\r\x0b\x0c]+")


def _ident_ok(s: str) -> bool:
    """Engine identifier rule: 1-8 ASCII alphanumerics."""
    return 1 <= len(s) <= 8 and s.isascii() and s.isalnum()


# Resource names of this many characters or more cap the lease lifetime.
_LONG_NAME = 6
_LONG_NAME_CAP = 100
_RECLAIM_GRACE = 10


class Resource:
    __slots__ = (
        "name", "holder", "expiry", "orig", "queue", "renews",
        "expired_holder", "grace_until",
    )

    def __init__(self, name: str):
        self.name = name
        self.holder: str | None = None
        self.expiry = 0
        self.orig = 0  # requested ttl of the current grant
        self.renews = 0  # renewals accepted on the current grant
        self.queue: list[tuple[str, int]] = []  # (client, ttl)
        self.expired_holder: str | None = None
        self.grace_until = 0


class Engine:
    def __init__(self, out=None):
        self.resources: list[Resource] = []
        self.by_name: dict[str, Resource] = {}  # keyed by lowercased name
        self.names: dict[str, str] = {}  # lowercased client -> first-accepted casing
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

    def _lifetime(self, r: Resource) -> int:
        """Effective lease lifetime from the requested ttl, the resource-name
        cap, and the renewals accepted on the current grant."""
        base = r.orig
        if len(r.name) >= _LONG_NAME:
            base = min(base, _LONG_NAME_CAP)
        return base - r.renews

    def _grant(self, r: Resource, client: str, ttl: int) -> None:
        r.holder = client
        r.orig = ttl
        r.renews = 0
        r.expiry = self.now + self._lifetime(r)
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
        parts = _TOKEN.findall(line)
        if not parts:
            return
        kind = parts[0]
        cid = parts[1] if len(parts) > 1 else ""
        cli_ok = _ident_ok(cid)
        echo = cid if cli_ok else "????????"
        rid = parts[2] if len(parts) > 2 else ""
        ckey = cid.lower()

        if kind == "A":
            if len(parts) < 4 or not cli_ok or not _ident_ok(rid):
                self._reject(echo, "FMT")
                return
            ttok = parts[3]
            if not (ttok.isascii() and ttok.isdigit() and 1 <= len(ttok) <= 3):
                self._reject(cid, "TTL")
                return
            ttl = int(ttok)
            if not 1 <= ttl <= 999:
                self._reject(cid, "TTL")
                return
            known = self.names.get(ckey)
            r = self.by_name.get(rid.lower())
            if r is not None and known is not None and (
                r.holder == known or any(w == known for w, _ in r.queue)
            ):
                self._reject(known, "STATE")
                return
            client = self.names.setdefault(ckey, cid)
            if r is None:
                r = Resource(rid)
                self.resources.append(r)
                self.by_name[rid.lower()] = r
            reclaim = r.expired_holder == client and self.now <= r.grace_until
            if r.holder is None:
                self._grant(r, client, ttl)
            else:
                if reclaim:
                    r.queue.insert(0, (client, ttl))
                else:
                    r.queue.append((client, ttl))
                self._emit(f"Q {len(r.queue)}")
            if reclaim:
                r.expired_holder = None
            self.c_acq += 1
            self.now += 1
            return

        if kind == "R":
            if len(parts) < 3 or not cli_ok or not _ident_ok(rid):
                self._reject(echo, "FMT")
                return
            canon = self.names.get(ckey)
            r = self.by_name.get(rid.lower())
            if r is None or canon is None or r.holder != canon:
                self._reject(canon if canon is not None else cid, "STATE")
                return
            if r.expiry <= self.now:  # lease is already due; no sweep has run yet
                self._reject(canon, "STATE")
                return
            r.renews += 1
            r.expiry = self.now + self._lifetime(r)
            self._emit(f"OK {self._holds_of(canon)}")
            self.c_ren += 1
            self.now += 1
            return

        if kind == "E":
            released = 0
            for r in self.resources:
                if r.holder is not None and r.expiry <= self.now:
                    r.expired_holder = r.holder
                    r.grace_until = self.now + _RECLAIM_GRACE
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
            canon = self.names.setdefault(ckey, cid)
            released = 0
            for r in self.resources:
                if r.holder == canon:
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
