"""ReflowCore greedy word-wrap layout engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
layout commands on stdin (``W`` sets the wrap width, ``A`` appends a word
with incremental layout, ``R`` reflows the whole document, ``D`` prints
the layout digest), writes one reply per command and an ``X`` trailer at
EOF. Format reference: ``docs/SPEC.md`` (note the drift warning at the
top of that file; the legacy engine's behavior is the contract).

Legacy behaviors reproduced here that the spec omits or gets wrong:

* tokens are separated by spaces only (tabs are part of a token); extra
  tokens after the expected ones are ignored;
* digits occupy no width when deciding whether a word fits (they still
  count towards the digest length);
* ``A`` joins the last line if ``fit + 1 + word_fit <= width``; a word
  wider than the width is accepted; a word appended to an empty line
  simply occupies it;
* ``R`` uses a strict ``<`` test, truncates (permanently, in the
  document) words wider than the width to ``width`` characters, stores
  line lengths without the joining spaces, and leaves one empty line for
  an empty document;
* ``W`` re-wraps only the last line (it may split, never merge) with the
  ``A`` rule and recomputes its length with spaces.
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


def _fit(word: str) -> int:
    return sum(1 for c in word if not c.isdigit())


class _Line:
    __slots__ = ("words", "length", "fit")

    def __init__(self) -> None:
        self.words: list[str] = []
        self.length = 0  # digest length
        self.fit = 0     # width used for the wrap test


class Engine:
    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[_Line] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        tokens = [t for t in line.split(" ") if t]
        cmd = line[:2]
        if line == "W" or cmd == "W ":
            reply = self._width(tokens)
        elif line == "A" or cmd == "A ":
            reply = self._append(tokens)
        elif line == "R" or cmd == "R ":
            reply = self._reflow()
        elif line == "D" or cmd == "D ":
            reply = self._digest()
        else:
            reply = "E FMT"
        if reply.startswith("E "):
            self.rejected += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.words} {self.reflows} {self.rejected}"

    def _place(self, lines: list[_Line], word: str, width: int) -> None:
        f = _fit(word)
        if lines and not lines[-1].words:
            last = lines[-1]
            last.words.append(word)
            last.length = len(word)
            last.fit = f
            return
        if lines and lines[-1].fit + 1 + f <= width:
            last = lines[-1]
            last.words.append(word)
            last.length += 1 + len(word)
            last.fit += 1 + f
            return
        new = _Line()
        new.words.append(word)
        new.length = len(word)
        new.fit = f
        lines.append(new)

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
        if self.lines and self.lines[-1].words:
            last = self.lines.pop()
            part: list[_Line] = []
            for word in last.words:
                self._place(part, word, v)
            self.lines.extend(part)
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        self.doc.append(word)
        self._place(self.lines, word, self.width)
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self) -> str:
        width = self.width
        self.doc = [w[:width] if _fit(w) > width else w for w in self.doc]
        lines: list[_Line] = [_Line()]
        for word in self.doc:
            f = _fit(word)
            last = lines[-1]
            if last.words and last.fit + 1 + f >= width:
                last = _Line()
                lines.append(last)
            if last.words:
                last.fit += 1 + f
            else:
                last.fit = f
            last.words.append(word)
            last.length += len(word)
        self.lines = lines
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self) -> str:
        total = sum(line.length * _WEIGHTS[i % 2]
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
