"""LockCore lease manager, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).

Engine behaviors the spec does not describe:

- Ids are case-insensitive; output uses the first spelling seen in an
  accepted command (rejects for FMT/TTL echo the raw token).
- Resources named with 6+ characters cap a granted ttl at 100.
- The n-th renewal of a grant sets ``expiry = now + ttl - n``.
- A lease whose expiry has passed can no longer be renewed, though it
  stays held until a sweep releases it.
- A client whose lease a sweep released, re-acquiring that resource
  within 10 ticks, is queued at the front of the wait queue (once).
- ``L`` for a client holding nothing is accepted: ``LEND 0``.
- Tokens past the ones a command uses are ignored.
"""

from __future__ import annotations

import sys

LONG_NAME = 6
LONG_TTL_CAP = 100
GRACE_TICKS = 10


def _valid_id(tok: str) -> bool:
    return 1 <= len(tok) <= 8 and tok.isascii() and tok.isalnum()


class Resource:
    __slots__ = ("name", "holder", "expiry", "orig", "renews", "queue", "grace")

    def __init__(self, name: str):
        self.name = name
        self.holder: str | None = None
        self.expiry = 0
        self.orig = 0
        self.renews = 0
        self.queue: list[tuple[str, int]] = []  # (client, ttl)
        self.grace: tuple[str, int] | None = None  # (client, release tick)


class Engine:
    def __init__(self, out=None):
        self.resources: list[Resource] = []
        self.by_name: dict[str, Resource] = {}
        self.clients: dict[str, str] = {}  # folded id -> display spelling
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

    def _client(self, tok: str) -> str:
        return self.clients.setdefault(tok.lower(), tok)

    def _holds_of(self, client: str) -> int:
        return sum(1 for r in self.resources if r.holder == client)

    def _grant(self, r: Resource, client: str, ttl: int) -> None:
        if len(r.name) >= LONG_NAME:
            ttl = min(ttl, LONG_TTL_CAP)
        r.holder = client
        r.orig = ttl
        r.renews = 0
        r.expiry = self.now + ttl
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
        raw = parts[1] if len(parts) > 1 else ""
        cli_ok = _valid_id(raw)
        echo = raw if cli_ok else "????????"
        known = self.clients.get(raw.lower(), raw)
        rid = parts[2] if len(parts) > 2 else ""

        if kind == "A":
            if len(parts) < 4 or not cli_ok or not _valid_id(rid):
                self._reject(echo, "FMT")
                return
            ttok = parts[3]
            if not (ttok.isascii() and ttok.isdigit() and 1 <= len(ttok) <= 3):
                self._reject(raw, "TTL")
                return
            ttl = int(ttok)
            if not 1 <= ttl <= 999:
                self._reject(raw, "TTL")
                return
            r = self.by_name.get(rid.lower())
            if r is not None and (
                r.holder == known or any(w == known for w, _ in r.queue)
            ):
                self._reject(known, "STATE")
                return
            cid = self._client(raw)
            if r is None:
                r = Resource(rid)
                self.resources.append(r)
                self.by_name[rid.lower()] = r
            reclaim = (
                r.grace is not None
                and r.grace[0] == cid
                and self.now - r.grace[1] <= GRACE_TICKS
            )
            if r.grace is not None and r.grace[0] == cid:
                r.grace = None
            if r.holder is None:
                self._grant(r, cid, ttl)
            else:
                if reclaim:
                    r.queue.insert(0, (cid, ttl))
                else:
                    r.queue.append((cid, ttl))
                self._emit(f"Q {len(r.queue)}")
            self.c_acq += 1
            self.now += 1
            return

        if kind == "R":
            if len(parts) < 3 or not cli_ok or not _valid_id(rid):
                self._reject(echo, "FMT")
                return
            r = self.by_name.get(rid.lower())
            if r is None or r.holder != known or r.expiry <= self.now:
                self._reject(known, "STATE")
                return
            r.renews += 1
            r.expiry = self.now + r.orig - r.renews
            self._emit(f"OK {self._holds_of(known)}")
            self.c_ren += 1
            self.now += 1
            return

        if kind == "E":
            released = 0
            for r in self.resources:
                if r.holder is not None and r.expiry <= self.now:
                    r.grace = (r.holder, self.now)
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
            cid = self._client(raw)
            released = 0
            for r in self.resources:
                if r.holder == cid:
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
