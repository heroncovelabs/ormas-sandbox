"""LockCore lease manager, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).

Engine behaviors reproduced here that the spec omits or gets wrong:

- input is read in 511-byte ``fgets`` chunks; each chunk is cut at the
  first NUL/CR/LF, empty chunks are skipped, and the rest is tokenized
  like ``sscanf("%7s %63s %63s %63s")`` (extra tokens are ignored);
- client and resource ids are case-insensitive; the first accepted
  spelling is the one printed;
- resources whose name is 6+ characters have their ttl capped at 100;
- each renewal shortens the lease's ttl by one more tick (k-th renewal
  sets ``expiry = now + ttl - k``);
- a lease whose expiry has been reached cannot be renewed, even before
  a sweep releases it;
- the client whose lease on a resource was most recently released by a
  sweep goes to the queue front if it queues for it again within
  ``GRACE`` ticks;
- ``L`` for a client holding nothing is accepted with ``LEND 0``.
"""

from __future__ import annotations

import sys

LINE_MAX = 512  # fgets buffer size, including the terminating NUL
LONG_NAME = 6  # resource names this long have their ttl capped
TTL_CAP = 100
GRACE = 10
QUEUE_MAX = 256  # a full wait queue rejects joiners with FMT
_WS = b" \t\n\v\f\r"
_ALNUM = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def _valid_id(tok: bytes) -> bool:
    return 1 <= len(tok) <= 8 and all(c in _ALNUM for c in tok)


def _scan(line: bytes) -> list[bytes]:
    """Emulate ``sscanf(line, "%7s %63s %63s %63s", ...)``."""
    toks: list[bytes] = []
    i, n = 0, len(line)
    for width in (7, 63, 63, 63):
        while i < n and line[i] in _WS:
            i += 1
        if i >= n:
            break
        j = i
        while j < n and j - i < width and line[j] not in _WS:
            j += 1
        toks.append(line[i:j])
        i = j
    return toks


class Resource:
    __slots__ = ("name", "holder", "expiry", "ttl", "renews", "queue", "lost")

    def __init__(self, name: str):
        self.name = name
        self.holder: str | None = None  # folded client key
        self.expiry = 0
        self.ttl = 0
        self.renews = 0
        self.queue: list[tuple[str, int]] = []  # (folded client key, ttl)
        self.lost: tuple[str, int] | None = None  # last sweep victim, tick


class Engine:
    def __init__(self, out=None):
        self.resources: list[Resource] = []
        self.by_name: dict[str, Resource] = {}
        self.clients: dict[str, str] = {}  # folded key -> first spelling
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

    def _register(self, cid: str) -> str:
        key = cid.lower()
        self.clients.setdefault(key, cid)
        return key

    def _display(self, cid: str) -> str:
        return self.clients.get(cid.lower(), cid)

    def _holds_of(self, key: str) -> int:
        return sum(1 for r in self.resources if r.holder == key)

    def _grant(self, r: Resource, key: str, ttl: int) -> None:
        if len(r.name) >= LONG_NAME:
            ttl = min(ttl, TTL_CAP)
        if r.lost is not None and r.lost[0] == key:
            r.lost = None  # the victim got its lease back
        r.holder = key
        r.ttl = ttl
        r.renews = 0
        r.expiry = self.now + ttl
        self._emit(f"G {r.name} {self.clients[key]}")

    def _drain_free(self) -> int:
        granted = 0
        for r in self.resources:  # creation order
            if r.holder is None and r.queue:
                key, ttl = r.queue.pop(0)
                self._grant(r, key, ttl)
                granted += 1
        return granted

    def handle_raw(self, chunk: bytes) -> None:
        for stop in (b"\0", b"\r", b"\n"):
            k = chunk.find(stop)
            if k >= 0:
                chunk = chunk[:k]
        if not chunk:
            return
        parts = _scan(chunk)
        if not parts:
            self._reject("????????", "FMT")
            return
        kind = parts[0]
        cbytes = parts[1] if len(parts) > 1 else b""
        cli_ok = _valid_id(cbytes)
        cid = cbytes.decode("latin-1")
        echo = cid if cli_ok else "????????"
        rbytes = parts[2] if len(parts) > 2 else b""
        res_ok = _valid_id(rbytes)
        rid = rbytes.decode("latin-1")

        if kind == b"A":
            if len(parts) < 4 or not cli_ok or not res_ok:
                self._reject(echo, "FMT")
                return
            ttok = parts[3]
            if not (1 <= len(ttok) <= 3 and ttok.isdigit()):
                self._reject(cid, "TTL")
                return
            ttl = int(ttok)
            if not 1 <= ttl <= 999:
                self._reject(cid, "TTL")
                return
            key = cid.lower()
            r = self.by_name.get(rid.lower())
            if r is not None and (
                r.holder == key or any(w == key for w, _ in r.queue)
            ):
                self._reject(self._display(cid), "STATE")
                return
            if r is not None and len(r.queue) >= QUEUE_MAX:
                self._reject(cid, "FMT")
                return
            key = self._register(cid)
            if r is None:
                r = Resource(rid)
                self.resources.append(r)
                self.by_name[rid.lower()] = r
            if r.holder is None:
                self._grant(r, key, ttl)
            else:
                if (
                    r.lost is not None
                    and r.lost[0] == key
                    and self.now - r.lost[1] <= GRACE
                ):
                    r.queue.insert(0, (key, ttl))
                else:
                    r.queue.append((key, ttl))
                self._emit(f"Q {len(r.queue)}")
            self.c_acq += 1
            self.now += 1
            return

        if kind == b"R":
            if len(parts) < 3 or not cli_ok or not res_ok:
                self._reject(echo, "FMT")
                return
            key = cid.lower()
            r = self.by_name.get(rid.lower())
            if r is None or r.holder != key or r.expiry <= self.now:
                self._reject(self._display(cid), "STATE")
                return
            r.renews += 1
            r.expiry = self.now + r.ttl - r.renews
            self._emit(f"OK {self._holds_of(key)}")
            self.c_ren += 1
            self.now += 1
            return

        if kind == b"E":
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

        if kind == b"L":
            if len(parts) < 2 or not cli_ok:
                self._reject(echo, "FMT")
                return
            key = self._register(cid)
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

    def handle(self, line: str) -> None:
        self.handle_raw(line.encode("latin-1", "replace"))

    def finish(self) -> None:
        self._emit(f"X {self.c_acq} {self.c_ren} {self.c_swp} {self.c_rej}")


def _chunks(stream):
    """Yield input the way ``fgets(buf, LINE_MAX, stdin)`` would."""
    while True:
        chunk = stream.readline(LINE_MAX - 1)
        if not chunk:
            return
        yield chunk


def main() -> None:
    engine = Engine()
    for chunk in _chunks(sys.stdin.buffer):
        engine.handle_raw(chunk)
    engine.finish()


if __name__ == "__main__":
    main()
