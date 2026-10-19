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


def _command_text(line: str) -> str:
    # The legacy reader ends a command at the first CR, LF, or C-string NUL.
    for terminator in ("\r", "\n", "\0"):
        line = line.partition(terminator)[0]
    return line


def _word_width(word: str) -> int:
    # Accepted words are ASCII alphanumeric; digits occupy zero wrap columns.
    return sum(char.isalpha() for char in word)


class Engine:
    """Stateful layout with the legacy engine's distinct layout paths."""

    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[list[str]] = []
        # Digest lengths and wrap columns differ, particularly after reflow.
        self._lengths: list[int] = []
        self._tail_width = 0
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        line = _command_text(line)
        # Only literal spaces separate tokens; extra arguments are ignored.
        tokens = [token for token in line.split(" ") if token][:2]
        if line == "W" or line.startswith("W "):
            reply = self._width(tokens)
        elif line == "A" or line.startswith("A "):
            reply = self._append(tokens)
        elif line == "R" or line.startswith("R "):
            reply = self._reflow(tokens[:1])
        elif line == "D" or line.startswith("D "):
            reply = self._digest(tokens[:1])
        else:
            reply = "E FMT"
        if reply.startswith("E "):
            self.rejected += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.words} {self.reflows} {self.rejected}"

    def _layout(
        self, words: list[str], *, reflow: bool = False
    ) -> tuple[list[list[str]], list[int], int]:
        # Both paths start with a line, including for an empty document.
        lines: list[list[str]] = [[]]
        lengths = [0]
        columns = 0
        for word in words:
            word_width = _word_width(word)
            separator = int(bool(lines[-1]))
            # Reflow reserves one extra column at the right edge. The first
            # word still fits unconditionally, even at the width limit.
            if separator and columns + 1 + word_width > self.width - int(reflow):
                lines.append([])
                lengths.append(0)
                columns = 0
                separator = 0
            columns += separator + word_width
            # Reflow's digest length omits its joining spaces. Future appends
            # count their own joining spaces normally.
            lengths[-1] += len(word) + (0 if reflow else separator)
            lines[-1].append(word)
        return lines, lengths, columns

    def _width(self, tokens: list[str]) -> str:
        if len(tokens) != 2:
            return "E FMT"
        w = tokens[1]
        # Leading zeroes are permitted within the three-digit token limit.
        if not (1 <= len(w) <= 3 and w.isascii() and w.isdigit()):
            return "E WIDTH"
        v = int(w)
        if not WIDTH_MIN <= v <= WIDTH_MAX:
            return "E WIDTH"
        self.width = v
        # A width command rewraps only the current last line, even when the
        # width is unchanged. Earlier line boundaries remain in place, and
        # this implicit layout does not increment the reflow counter.
        if self.lines:
            lines, lengths, self._tail_width = self._layout(self.lines[-1])
            self.lines[-1:] = lines
            self._lengths[-1:] = lengths
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) != 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        self.doc.append(word)
        word_width = _word_width(word)
        if (not self.lines or
                (self.lines[-1] and
                 self._tail_width + 1 + word_width > self.width)):
            self.lines.append([])
            self._lengths.append(0)
            self._tail_width = 0
        separator = int(bool(self.lines[-1]))
        self._tail_width += separator + word_width
        self._lengths[-1] += separator + len(word)
        self.lines[-1].append(word)
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self, tokens: list[str]) -> str:
        if len(tokens) != 1:
            return "E FMT"
        # Visually overlong words are permanently clipped by character
        # count. Digits affect the clipping test through their zero width,
        # while the slice itself counts every character.
        self.doc = [word[:self.width] if _word_width(word) > self.width else word
                    for word in self.doc]
        self.lines, self._lengths, self._tail_width = self._layout(
            self.doc, reflow=True
        )
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self, tokens: list[str]) -> str:
        if len(tokens) != 1:
            return "E FMT"
        total = sum(length * _WEIGHTS[i % 2]
                    for i, length in enumerate(self._lengths))
        return f"D {total % DIGEST_MOD}"


def process(lines: Iterable[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = _command_text(raw)
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # The legacy fgets reader consumes at most 65535 bytes per command.
    # Read bytes to preserve embedded CRs and this limit even for non-ASCII
    # input. Latin-1 decoding keeps every byte available to ASCII validation.
    chunks = iter(lambda: sys.stdin.buffer.readline(65535), b"")
    process((chunk.decode("latin-1") for chunk in chunks), out=sys.stdout)


if __name__ == "__main__":
    main()
