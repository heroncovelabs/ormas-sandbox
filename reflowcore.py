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


class Engine:
    """Layout engine preserving the legacy's distinct layout paths."""

    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[list[str]] = []
        # Digest lengths are cached separately: reflow omits joining spaces,
        # while append adds them and width changes rebuild them.
        self.lengths: list[int] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # Only literal spaces separate tokens; surplus tokens are ignored.
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

    @staticmethod
    def _line_len(line: list[str]) -> int:
        return sum(len(w) for w in line) + max(0, len(line) - 1)

    @staticmethod
    def _word_width(word: str) -> int:
        # Digits occupy bytes in the digest but consume zero wrap width.
        return sum(c.isalpha() for c in word)

    @classmethod
    def _wrap_len(cls, line: list[str]) -> int:
        return sum(cls._word_width(w) for w in line) + max(0, len(line) - 1)

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
        # Only the current last line is rewrapped. Earlier lines retain both
        # their boundaries and cached digest lengths. This path retains
        # oversized words and counts joining spaces on the rebuilt tail.
        if self.lines:
            tail = self.lines.pop()
            self.lengths.pop()
            current: list[str] = []
            for word in tail:
                if (current and
                        self._wrap_len(current) + 1 + self._word_width(word) > v):
                    self.lines.append(current)
                    self.lengths.append(self._line_len(current))
                    current = []
                current.append(word)
            self.lines.append(current)
            self.lengths.append(self._line_len(current))
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        self.doc.append(word)
        if self.lines and not self.lines[-1]:
            self.lines[-1].append(word)
            self.lengths[-1] = len(word)
        elif (self.lines and
                self._wrap_len(self.lines[-1]) + 1 + self._word_width(word)
                <= self.width):
            self.lines[-1].append(word)
            self.lengths[-1] += 1 + len(word)
        else:
            self.lines.append([word])
            self.lengths.append(len(word))
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self, tokens: list[str]) -> str:
        # Reflow permanently shortens words whose wrap width is oversized.
        # The cutoff is a byte count, even for mixed letter/digit words.
        self.doc = [word[:self.width] if self._word_width(word) > self.width
                    else word for word in self.doc]
        self.lines = [[]]
        self.lengths = [0]
        for word in self.doc:
            # Equality starts a new line here; append and W allow equality.
            if (self.lines[-1] and
                    self._wrap_len(self.lines[-1]) + 1 + self._word_width(word)
                    >= self.width):
                self.lines.append([])
                self.lengths.append(0)
            self.lines[-1].append(word)
            self.lengths[-1] += len(word)
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self, tokens: list[str]) -> str:
        total = sum(length * _WEIGHTS[i % 2]
                    for i, length in enumerate(self.lengths))
        return f"D {total % DIGEST_MOD}"


def process(lines: Iterable[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        # The legacy reader terminates commands at CR, LF, or NUL.
        line = raw.split("\0", 1)[0].split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Match the legacy 64 KiB fgets buffer and preserve embedded CR bytes.
    chunks = iter(lambda: sys.stdin.buffer.readline(65535), b"")
    process((raw.decode("ascii", "surrogateescape") for raw in chunks),
            out=sys.stdout)


if __name__ == "__main__":
    main()
