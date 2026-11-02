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
# The legacy input buffer holds at most this many bytes per read.
_INPUT_CHUNK_BYTES = 65535


def _valid_word(token: str) -> bool:
    return 1 <= len(token) <= WORD_MAX and token.isascii() and token.isalnum()


def _command_prefix(line: str) -> str:
    """Return the part of a physical input line processed by the engine."""
    return line.split("\n", 1)[0].split("\r", 1)[0].split("\0", 1)[0]


def _word_occupancy(word: str) -> int:
    """Count the characters of a word that occupy wrap space."""
    return sum("A" <= char <= "Z" or "a" <= char <= "z" for char in word)


class _LayoutLine(list[str]):
    """Rendered words with independent wrap and digest contributions."""

    def __init__(self) -> None:
        super().__init__()
        self.wrap_length = 0
        self.digest_length = 0

    def append(self, word: str, *, reflow: bool = False) -> None:
        space = int(bool(self))
        self.wrap_length += space + _word_occupancy(word)
        # Reflow counts token lengths but omits its joining spaces. Later
        # incremental appends contribute their joining spaces as usual.
        self.digest_length += len(word) + (0 if reflow else space)
        super().append(word)


class Engine:
    """Layout with separate incremental and full-reflow bookkeeping."""

    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[_LayoutLine] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # The engine terminates a command at a carriage return or NUL and
        # separates its tokens using ASCII spaces only.
        line = _command_prefix(line)
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
        # A resize rewraps only the last rendered line. Earlier lines and
        # their digest bookkeeping survive unchanged, even at a wider width.
        if self.lines:
            old_line = self.lines.pop()
            self.lines.append(_LayoutLine())
            for word in old_line:
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

    def _place(self, word: str, *, reflow: bool = False) -> None:
        if not self.lines:
            self.lines.append(_LayoutLine())
        line = self.lines[-1]
        needed = line.wrap_length + 1 + _word_occupancy(word)
        # Full reflow breaks on exact fits; append and resize allow them.
        if line and (needed > self.width or (reflow and needed == self.width)):
            line = _LayoutLine()
            self.lines.append(line)
        line.append(word, reflow=reflow)

    def _reflow(self, tokens: list[str]) -> str:
        # Reflow always leaves at least one line, even for an empty document.
        self.lines = [_LayoutLine()]
        for i, word in enumerate(self.doc):
            if _word_occupancy(word) > self.width:
                # The legacy engine clips bytes by width only when the
                # alphabetic occupancy overflows, and keeps the clipped word.
                word = self.doc[i] = word[:self.width]
            self._place(word, reflow=True)
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self, tokens: list[str]) -> str:
        total = sum(line.digest_length * _WEIGHTS[i % 2]
                    for i, line in enumerate(self.lines))
        return f"D {total % DIGEST_MOD}"


def process(lines: Iterable[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = _command_prefix(raw)
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Match the byte-oriented, bounded reads of the legacy input buffer.
    # Latin-1 preserves each byte so non-ASCII input follows the reject path.
    chunks = iter(lambda: sys.stdin.buffer.readline(_INPUT_CHUNK_BYTES), b"")
    process((chunk.decode("latin-1") for chunk in chunks), out=sys.stdout)


if __name__ == "__main__":
    main()
