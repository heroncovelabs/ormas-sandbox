"""ReflowCore greedy word-wrap layout engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
layout commands on stdin (``W`` sets the wrap width, ``A`` appends a word
with incremental layout, ``R`` reflows the whole document, ``D`` prints
the layout digest), writes one reply per command and an ``X`` trailer at
EOF. Format reference: ``docs/SPEC.md`` (note the drift warning at the
top of that file; the legacy engine's behavior is the contract).

Legacy behaviors reproduced here that differ from the spec:

- Tokens are split on single spaces only (runs of spaces collapse; tabs
  are part of a token). Extra trailing tokens are ignored by every
  command.
- Digits have zero width when fitting words on a line (and when deciding
  whether a word is too wide); the digest still counts every character.
- ``A`` accepts words wider than the current width.
- ``W`` re-lays the words of the last line (only) at the new width.
- ``R`` truncates words wider than the width to their first ``width``
  characters (permanently, in the document), fits with a strict ``<``,
  and records line lengths without the joining spaces. Reflowing an
  empty document yields one empty line.
"""

from __future__ import annotations

import sys

WORD_MAX = 16
WIDTH_MIN = 10
WIDTH_MAX = 120
DIGEST_MOD = 1000003
_WEIGHTS = (3, 5)


def _valid_word(token: str) -> bool:
    return 1 <= len(token) <= WORD_MAX and token.isascii() and token.isalnum()


def _measure(word: str) -> int:
    """Width of a word for fitting: digits take no room."""
    return sum(1 for c in word if not c.isdigit())


class Line:
    __slots__ = ("words", "disp", "meas")

    def __init__(self) -> None:
        self.words: list[int] = []  # indices into the document
        self.disp = 0  # length as counted by the digest
        self.meas = 0  # width as counted when fitting words


class Engine:
    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[Line] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        cmd = line[0]
        if cmd in "WARD" and (len(line) == 1 or line[1] == " "):
            tokens = [t for t in line.split(" ") if t]
            if cmd == "W":
                reply = self._width(tokens)
            elif cmd == "A":
                reply = self._append(tokens)
            elif cmd == "R":
                reply = self._reflow()
            else:
                reply = self._digest()
        else:
            reply = "E FMT"
        if reply.startswith("E "):
            self.rejected += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.words} {self.reflows} {self.rejected}"

    def _place(self, idx: int) -> None:
        """Incremental greedy placement (``<=``, spaces counted)."""
        word = self.doc[idx]
        last = self.lines[-1] if self.lines else None
        if last is not None and not last.words:
            last.words.append(idx)
            last.disp = len(word)
            last.meas = _measure(word)
        elif (last is not None and
                last.meas + 1 + _measure(word) <= self.width):
            last.words.append(idx)
            last.disp += 1 + len(word)
            last.meas += 1 + _measure(word)
        else:
            new = Line()
            new.words.append(idx)
            new.disp = len(word)
            new.meas = _measure(word)
            self.lines.append(new)

    def _width(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        w = tokens[1]
        if not (2 <= len(w) <= 3 and w.isascii() and w.isdigit()):
            return "E WIDTH"
        v = int(w)
        if not WIDTH_MIN <= v <= WIDTH_MAX:
            return "E WIDTH"
        self.width = v
        # only the last line is re-laid at the new width
        if self.lines and self.lines[-1].words:
            last = self.lines.pop()
            self.lines.append(Line())
            for idx in last.words:
                self._place(idx)
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        self.doc.append(word)
        self._place(len(self.doc) - 1)
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self) -> str:
        self.lines = []
        if not self.doc:
            self.lines.append(Line())
        for idx, word in enumerate(self.doc):
            if _measure(word) > self.width:
                word = self.doc[idx] = word[:self.width]
            m = _measure(word)
            if self.lines and self.lines[-1].meas + 1 + m < self.width:
                last = self.lines[-1]
                last.words.append(idx)
                last.disp += len(word)
                last.meas += 1 + m
            else:
                new = Line()
                new.words.append(idx)
                new.disp = len(word)
                new.meas = m
                self.lines.append(new)
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self) -> str:
        total = sum(line.disp * _WEIGHTS[i % 2]
                    for i, line in enumerate(self.lines))
        return f"D {total % DIGEST_MOD}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    process(sys.stdin.readlines(), out=sys.stdout)


if __name__ == "__main__":
    main()
