"""ReflowCore greedy word-wrap layout engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
layout commands on stdin (``W`` sets the wrap width, ``A`` appends a word
with incremental layout, ``R`` reflows the whole document, ``D`` prints
the layout digest), writes one reply per command and an ``X`` trailer at
EOF. Format reference: ``docs/SPEC.md`` (note the drift warning at the
top of that file; the legacy engine's behavior is the contract).
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


def _fit_width(word: str) -> int:
    # Engine: digits occupy no width when fitting words onto a line.
    return sum(1 for c in word if not c.isdigit())


class _Line:
    """A laid-out line: its words, the length the digest uses, and the
    width the wrap rule fits against."""

    __slots__ = ("words", "length", "fit")

    def __init__(self, words: list[str], length: int, fit: int) -> None:
        self.words = words
        self.length = length
        self.fit = fit


def _lay_incremental(lines: list[_Line], word: str, width: int) -> None:
    w = _fit_width(word)
    if lines and lines[-1].fit + 1 + w <= width:
        last = lines[-1]
        last.words.append(word)
        last.length += 1 + len(word)
        last.fit += 1 + w
    else:
        lines.append(_Line([word], len(word), w))


class Engine:
    """Layout engine reproducing the legacy binary's behavior."""

    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[_Line] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # Engine: tokens are separated by spaces only.
        tokens = [t for t in line.split(" ") if t]
        if line == "W" or line.startswith("W "):
            reply = self._width(tokens)
        elif line == "A" or line.startswith("A "):
            reply = self._append(tokens)
        elif line == "R" or line.startswith("R "):
            reply = self._reflow(tokens)
        elif line == "D" or line.startswith("D "):
            reply = self._digest(tokens)
        else:
            reply = "E FMT"
        if reply.startswith("E "):
            self.rejected += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.words} {self.reflows} {self.rejected}"

    # Engine: extra trailing tokens are ignored on every command.

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
        # Engine: the last line is re-laid incrementally at the new width.
        if self.lines:
            relaid: list[_Line] = []
            for word in self.lines.pop().words:
                _lay_incremental(relaid, word, v)
            self.lines.extend(relaid)
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        self.doc.append(word)
        _lay_incremental(self.lines, word, self.width)
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self, tokens: list[str]) -> str:
        width = self.width
        # Engine: words too wide for the current width are cut to it.
        self.doc = [word[:width] if _fit_width(word) > width else word
                    for word in self.doc]
        # Engine: reflow fits strictly below the width and its lines'
        # digest length leaves out the joining spaces.
        self.lines = []
        for word in self.doc:
            w = _fit_width(word)
            if self.lines and self.lines[-1].fit + 1 + w < width:
                last = self.lines[-1]
                last.words.append(word)
                last.length += len(word)
                last.fit += 1 + w
            else:
                self.lines.append(_Line([word], len(word), w))
        self.reflows += 1
        return f"L {max(1, len(self.lines))}"

    def _digest(self, tokens: list[str]) -> str:
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
