"""SchedCore dependency scheduler, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).

Engine behavior reproduced here where it differs from the spec:

- Input is read in fgets-sized chunks (511 bytes); blank chunks are
  skipped, whitespace-only ones are rejected ``FMT``.
- Tokens are scanned like ``sscanf("%7s %63s %63s %127s")``: extra
  trailing tokens are ignored, over-long tokens spill into the next field.
- Job ids are case-insensitive; the first-defined spelling is kept and
  echoed for ``DUP`` and ``STATE`` rejects of existing jobs.
- Repeated dependency entries are accepted and collapsed.
- Every invalidation (direct failure or cascade) moves the job to the
  front of its priority tier (most recently invalidated first), and each
  invalidation after the first costs 7 priority points (floor 1).
- Never-invalidated jobs with two or more distinct dependencies and a
  priority that is a multiple of 10 win ties at their priority.
- A job with a dependency that is undefined when a ``G`` examines it is
  blocked permanently.
"""

from __future__ import annotations

import sys

LINE_MAX = 511  # fgets(buf, 512, stdin)
FIELD_WIDTHS = (7, 63, 63, 127)
WS = b" \t\n\v\f\r"
PENALTY = 7


def _scan(line: bytes) -> list[bytes]:
    """Emulate sscanf("%7s %63s %63s %127s")."""
    fields: list[bytes] = []
    i, n = 0, len(line)
    for width in FIELD_WIDTHS:
        while i < n and line[i] in WS:
            i += 1
        if i >= n:
            break
        j = i
        while j < n and j - i < width and line[j] not in WS:
            j += 1
        fields.append(line[i:j])
        i = j
    return fields


def _valid_id(tok: str) -> bool:
    return 1 <= len(tok) <= 8 and tok.isascii() and tok.isalnum()


class Job:
    __slots__ = (
        "name", "key", "prio", "deps", "order", "executed", "invalidations",
        "fanin", "stale",
    )

    def __init__(self, name: str, prio: int, deps: list[str], defseq: int):
        self.name = name
        self.key = name.lower()
        self.prio = prio
        self.deps = deps  # lowercase keys, distinct
        self.order = defseq
        self.executed = False
        self.invalidations = 0
        self.fanin = len(deps) >= 2
        self.stale = False

    def eff_prio(self) -> int:
        if self.invalidations <= 1:
            return self.prio
        return max(1, self.prio - PENALTY * (self.invalidations - 1))

    def boosted(self) -> bool:
        return self.invalidations == 0 and self.fanin and self.prio % 10 == 0


class Engine:
    def __init__(self, out=None):
        self.jobs: list[Job] = []
        self.by_key: dict[str, Job] = {}
        self.def_next = 1
        self.inv_next = 1
        self.c_def = 0
        self.c_exec = 0
        self.c_fail = 0
        self.c_rej = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, echo: str, code: str) -> None:
        self._emit(f"R {echo} {code}")
        self.c_rej += 1

    def _deps_ready(self, j: Job) -> bool:
        if j.stale:
            return False
        for d in j.deps:
            k = self.by_key.get(d)
            if k is None:
                j.stale = True
                return False
            if not k.executed:
                return False
        return True

    def handle(self, raw: bytes) -> None:
        for idx, ch in enumerate(raw):
            if ch in b"\r\n":
                line = raw[:idx]
                break
        else:
            line = raw
        if not line:
            return
        parts = [p.decode("latin-1") for p in _scan(line)]
        if not parts:
            self._reject("????????", "FMT")
            return
        kind = parts[0]
        job = parts[1] if len(parts) > 1 else ""
        job_ok = _valid_id(job)
        echo = job if job_ok else "????????"

        if kind == "J":
            if len(parts) < 4 or not job_ok:
                self._reject(echo, "FMT")
                return
            ptok = parts[2]
            if not (ptok.isascii() and ptok.isdigit() and 1 <= len(ptok) <= 2):
                self._reject(job, "PRIO")
                return
            prio = int(ptok)
            if not 1 <= prio <= 99:
                self._reject(job, "PRIO")
                return
            dtok = parts[3]
            key = job.lower()
            deps: list[str] = []
            bad = False
            if dtok != "0":
                for part in dtok.split(","):
                    if not _valid_id(part):
                        bad = True
                        break
                    dk = part.lower()
                    if dk == key:  # self-dependency
                        bad = True
                        break
                    if dk not in deps:
                        deps.append(dk)
            if bad:
                self._reject(job, "DEPS")
                return
            existing = self.by_key.get(key)
            if existing is not None:
                self._reject(existing.name, "DUP")
                return
            j = Job(job, prio, deps, self.def_next)
            self.def_next += 1
            self.jobs.append(j)
            self.by_key[key] = j
            self.c_def += 1
            self._emit(f"OK {self.c_def}")
            return

        if kind == "G":
            executed_this = 0
            while True:
                best: Job | None = None
                best_rank = None
                for j in self.jobs:
                    if j.executed:
                        continue
                    if not self._deps_ready(j):
                        continue
                    rank = (-j.eff_prio(), not j.boosted(), j.order)
                    if best is None or rank < best_rank:
                        best = j
                        best_rank = rank
                if best is None:
                    break
                best.executed = True
                self.c_exec += 1
                executed_this += 1
                self._emit(f"E {best.name}")
            blocked = sum(1 for j in self.jobs if not j.executed)
            self._emit(f"GEND {executed_this} {blocked}")
            return

        if kind == "F":
            if len(parts) < 2 or not job_ok:
                self._reject(echo, "FMT")
                return
            j = self.by_key.get(job.lower())
            if j is None or not j.executed:
                self._reject(j.name if j is not None else job, "STATE")
                return
            self._invalidate(j)
            invalidated = {j.key}
            count = 1
            changed = True
            while changed:
                changed = False
                for k in self.jobs:
                    if not k.executed:
                        continue
                    if any(d in invalidated for d in k.deps):
                        self._invalidate(k)
                        invalidated.add(k.key)
                        count += 1
                        changed = True
            self.c_fail += 1
            self._emit(f"OK {count}")
            return

        self._reject(echo, "FMT")

    def _invalidate(self, j: Job) -> None:
        j.executed = False
        j.invalidations += 1
        j.order = -self.inv_next
        self.inv_next += 1

    def finish(self) -> None:
        self._emit(f"X {self.c_def} {self.c_exec} {self.c_fail} {self.c_rej}")


def _chunks(data: bytes):
    """Split input the way repeated fgets(buf, 512) calls would."""
    i, n = 0, len(data)
    while i < n:
        nl = data.find(b"\n", i, i + LINE_MAX)
        end = nl + 1 if nl != -1 else min(i + LINE_MAX, n)
        yield data[i:end]
        i = end


def main() -> None:
    engine = Engine()
    for chunk in _chunks(sys.stdin.buffer.read()):
        engine.handle(chunk)
    engine.finish()
    sys.stdout.flush()


if __name__ == "__main__":
    main()
