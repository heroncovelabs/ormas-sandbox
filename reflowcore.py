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
from collections.abc import Iterable

WORD_MAX = 16
WIDTH_MIN = 10
WIDTH_MAX = 120
DIGEST_MOD = 1000003
_WEIGHTS = (3, 5)


def _valid_word(token: str) -> bool:
    return 1 <= len(token) <= WORD_MAX and token.isascii() and token.isalnum()


def _word_width(word: str) -> int:
    """Digits occupy bytes in a digest, but have zero layout width."""
    return sum("A" <= c <= "Z" or "a" <= c <= "z" for c in word)


class Engine:
    """Keep the legacy engine's distinct incremental and reflow layouts."""

    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[list[str]] = []
        self._widths: list[int] = []
        # Reflow omits joining spaces from these cached digest lengths.
        self._lengths: list[int] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # Only ASCII spaces delimit fields; surplus fields are ignored.
        tokens = [token for token in line.split(" ") if token]
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

    def _place(self, word: str, *, reflow: bool = False) -> None:
        width = _word_width(word)
        limit = self.width - int(reflow)
        if (not self.lines or
                (self.lines[-1] and self._widths[-1] + 1 + width > limit)):
            self.lines.append([])
            self._widths.append(0)
            self._lengths.append(0)
        if self.lines[-1]:
            self._widths[-1] += 1
            if not reflow:
                self._lengths[-1] += 1
        self.lines[-1].append(word)
        self._widths[-1] += width
        self._lengths[-1] += len(word)

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
        # A resize rebuilds just the tail, using incremental layout. Earlier
        # lines (including their cached digest lengths) remain untouched.
        if self.lines and self.lines[-1]:
            tail = self.lines[-1]
            self.lines[-1] = []
            self._widths[-1] = 0
            self._lengths[-1] = 0
            for word in tail:
                self._place(word)
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        self.doc.append(word)
        self._place(word)
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self, tokens: list[str]) -> str:
        # Clipping tests layout width, then takes a byte-counted prefix. The
        # shortened words become the document for all subsequent commands.
        self.doc = [word[:self.width] if _word_width(word) > self.width else word
                    for word in self.doc]
        self.lines = [[]]
        self._widths = [0]
        self._lengths = [0]
        for word in self.doc:
            self._place(word, reflow=True)
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self, tokens: list[str]) -> str:
        total = sum(length * _WEIGHTS[i % 2]
                    for i, length in enumerate(self._lengths))
        return f"D {total % DIGEST_MOD}"


def process(lines: Iterable[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        # The reference treats CR and NUL as record terminators, discarding
        # the rest of that input record before splitting its fields.
        line = raw.split("\x00", 1)[0].split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Match the legacy 65536-byte fgets buffer, including partial records.
    records = iter(lambda: sys.stdin.buffer.readline(65535), b"")
    process((raw.decode("utf-8", "surrogateescape") for raw in records),
            out=sys.stdout)


if __name__ == "__main__":
    main()
