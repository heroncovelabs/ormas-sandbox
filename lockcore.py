"""LockCore lease manager, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).

Engine behaviors that differ from the spec, reproduced here:

- ids are case-insensitive; the spelling first seen on an accepted
  command is the one echoed back from then on;
- stray trailing tokens are ignored;
- resources whose name is 6+ characters cap the ttl at 100;
- every renewal of a grant shortens its ttl by one more tick;
- a lease whose expiry has been reached can no longer be renewed, even
  before a sweep releases it;
- the client that last lost a resource to a sweep jumps to the head of
  its wait queue if it re-acquires within 10 ticks of that sweep;
- ``L`` for a client holding nothing is accepted: ``LEND 0``.
"""

from __future__ import annotations

import sys

LONG_NAME = 6
LONG_TTL_CAP = 100
GRACE_TICKS = 10


class Resource:
    __slots__ = ("name", "holder", "expiry", "orig", "renews", "queue", "lost")

    def __init__(self, name: str):
        self.name = name
        self.holder: str | None = None  # client key (case-folded)
        self.expiry = 0
        self.orig = 0
        self.renews = 0
        self.queue: list[tuple[str, int]] = []  # (client key, ttl)
        self.lost: tuple[str, int] | None = None  # (client key, sweep tick)


def _valid_id(tok: str) -> bool:
    return 1 <= len(tok) <= 8 and tok.isascii() and tok.isalnum()


class Engine:
    def __init__(self, out=None):
        self.resources: list[Resource] = []
        self.by_name: dict[str, Resource] = {}
        self.clients: dict[str, str] = {}  # key -> display spelling
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

    def _display(self, cid: str) -> str:
        return self.clients.get(cid.lower(), cid)

    def _register(self, cid: str) -> str:
        return self.clients.setdefault(cid.lower(), cid)

    def _holds_of(self, key: str) -> int:
        return sum(1 for r in self.resources if r.holder == key)

    def _grant(self, r: Resource, key: str, ttl: int) -> None:
        r.holder = key
        r.orig = min(ttl, LONG_TTL_CAP) if len(r.name) >= LONG_NAME else ttl
        r.renews = 0
        r.expiry = self.now + r.orig
        self._emit(f"G {r.name} {self.clients[key]}")

    def _drain_free(self) -> int:
        granted = 0
        for r in self.resources:  # creation order
            if r.holder is None and r.queue:
                key, ttl = r.queue.pop(0)
                self._grant(r, key, ttl)
                granted += 1
        return granted

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        cid = parts[1] if len(parts) > 1 else ""
        cli_ok = _valid_id(cid)
        echo = cid if cli_ok else "????????"
        key = cid.lower()
        rid = parts[2] if len(parts) > 2 else ""

        if kind == "A":
            if len(parts) < 4 or not cli_ok or not _valid_id(rid):
                self._reject(echo, "FMT")
                return
            ttok = parts[3]
            if not (ttok.isascii() and ttok.isdigit() and 1 <= len(ttok) <= 3):
                self._reject(echo, "TTL")
                return
            ttl = int(ttok)
            if not 1 <= ttl <= 999:
                self._reject(echo, "TTL")
                return
            r = self.by_name.get(rid.lower())
            if r is not None and (
                r.holder == key or any(w == key for w, _ in r.queue)
            ):
                self._reject(self._display(cid), "STATE")
                return
            self._register(cid)
            if r is None:
                r = Resource(rid)
                self.resources.append(r)
                self.by_name[rid.lower()] = r
            graced = (
                r.lost is not None
                and r.lost[0] == key
                and self.now - r.lost[1] <= GRACE_TICKS
            )
            if r.lost is not None and r.lost[0] == key:
                r.lost = None  # the reclaim slot is single-use
            if r.holder is None:
                self._grant(r, key, ttl)
            else:
                if graced:
                    r.queue.insert(0, (key, ttl))
                else:
                    r.queue.append((key, ttl))
                self._emit(f"Q {len(r.queue)}")
            self.c_acq += 1
            self.now += 1
            return

        if kind == "R":
            if len(parts) < 3 or not cli_ok or not _valid_id(rid):
                self._reject(echo, "FMT")
                return
            r = self.by_name.get(rid.lower())
            if r is None or r.holder != key or r.expiry <= self.now:
                self._reject(self._display(cid), "STATE")
                return
            r.renews += 1
            r.expiry = self.now + r.orig - r.renews
            self._emit(f"OK {self._holds_of(key)}")
            self.c_ren += 1
            self.now += 1
            return

        if kind == "E":
            released = 0
            for r in self.resources:
                if r.holder is not None and r.expiry <= self.now:
                    r.lost = (r.holder, self.now)
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
            self._register(cid)
            released = 0
            for r in self.resources:
                if r.holder == key:
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
