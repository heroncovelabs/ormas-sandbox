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


def _word_width(word: str) -> int:
    # Digits are stored and digested, but consume no wrap width.
    return sum(c.isalpha() for c in word)


class Engine:
    """Layout engine with the legacy incremental and full-reflow paths."""

    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[list[str]] = []
        # Reflow omits joining spaces from these cached digest lengths.
        # Appends add their own spaces; W refreshes the current last line.
        self._digest_lengths: list[int] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # Only literal spaces separate fields, and the command must start
        # in column zero. Additional fields after the operand are ignored.
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
    def _line_width(line: list[str]) -> int:
        return sum(_word_width(w) for w in line) + max(0, len(line) - 1)

    def _wrap(self, words: list[str], *, strict: bool) -> list[list[str]]:
        # An empty full reflow still creates one empty line.
        lines: list[list[str]] = [[]]
        for word in words:
            needed = self._line_width(lines[-1]) + 1 + _word_width(word)
            fits = needed < self.width if strict else needed <= self.width
            if not lines[-1] or fits:
                lines[-1].append(word)
            else:
                lines.append([word])
        return lines

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
        # Only the current last line is rewrapped. Earlier lines and their
        # cached digest lengths survive width changes, even widening.
        if self.lines:
            last = self.lines.pop()
            self._digest_lengths.pop()
            wrapped = self._wrap(last, strict=False)
            self.lines.extend(wrapped)
            self._digest_lengths.extend(self._line_len(line) for line in wrapped)
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        self.doc.append(word)
        if (self.lines and
                (not self.lines[-1] or
                 self._line_width(self.lines[-1]) + 1 + _word_width(word)
                 <= self.width)):
            self._digest_lengths[-1] += len(word) + bool(self.lines[-1])
            self.lines[-1].append(word)
        else:
            self.lines.append([word])
            self._digest_lengths.append(len(word))
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self, tokens: list[str]) -> str:
        # Overwide words are permanently shortened to a raw-character
        # prefix. The decision to shorten uses their wrap width.
        self.doc = [word[:self.width] if _word_width(word) > self.width else word
                    for word in self.doc]
        self.lines = self._wrap(self.doc, strict=True)
        self._digest_lengths = [sum(len(word) for word in line)
                                for line in self.lines]
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self, tokens: list[str]) -> str:
        total = sum(length * _WEIGHTS[i % 2]
                    for i, length in enumerate(self._digest_lengths))
        return f"D {total % DIGEST_MOD}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        # The legacy reader ends commands at LF and treats CR and NUL as
        # the end of the command text, discarding the rest of that line.
        line = raw.split("\n", 1)[0].split("\r", 1)[0].split("\0", 1)[0]
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Byte-preserving input also keeps CR inside a physical LF-delimited
    # line. Non-ASCII operand bytes are rejected by the field validators.
    process(sys.stdin.buffer.read().decode("latin-1").split("\n"), out=sys.stdout)


if __name__ == "__main__":
    main()
