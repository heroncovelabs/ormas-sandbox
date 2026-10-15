"""ReflowCore greedy word-wrap layout engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
layout commands on stdin (``W`` sets the wrap width, ``A`` appends a word
with incremental layout, ``R`` reflows the whole document, ``D`` prints
the layout digest), writes one reply per command and an ``X`` trailer at
EOF. Format reference: ``docs/SPEC.md`` (note the drift warning at the
top of that file; the legacy engine's behavior is the contract).

Behavior notes (observed from the legacy engine, which is the contract;
they differ from the spec in places):

* Parsing: ``W`` and ``A`` need a token after the command word and ignore
  any extra tokens; ``R`` and ``D`` ignore their arguments entirely.
* Cost: a word's wrap cost counts only its letters; digits take no room.
  Incremental append joins a word when ``fit + 1 + cost <= width``.
  Reflow joins only when ``fit + 1 + cost < width``.
* Words are accepted regardless of the current width.
* Reflow clips a word whose letters exceed the width to ``width`` letters
  and weighs it as ``width`` characters.
* Digest: each line weighs its words' lengths plus one space between
  consecutive words, except that a line built by a reflow weighs only the
  sum of its word lengths until the next ``W`` command.
* A ``W`` command re-wraps every existing line on its own at the new
  width (lines are never merged), using the incremental rule.
* A reflow of an empty document leaves one empty line, which the next
  append fills unconditionally.
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


def _cost(word: str) -> int:
    """Wrap cost of a word: its letters (digits take no room)."""
    return sum(1 for ch in word if ch.isalpha())


class _Line:
    """A line: its words as (cost, length) pairs, and its digest weight."""

    __slots__ = ("items", "dig")

    def __init__(self) -> None:
        self.items: list[tuple[int, int]] = []
        self.dig = 0

    @property
    def fit(self) -> int:
        if not self.items:
            return 0
        return sum(c for c, _ in self.items) + len(self.items) - 1


class Engine:
    """Layout engine: incremental append is an optimization of reflow."""

    def __init__(self) -> None:
        self.width = 40
        self.lines: list[_Line] = []
        self.doc: list[str] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        tokens = line.split()
        if line == "W" or line.startswith("W "):
            reply = self._width(tokens)
        elif line == "A" or line.startswith("A "):
            reply = self._append(tokens)
        elif line == "R" or line.startswith("R "):
            reply = self._reflow()
        elif line == "D" or line.startswith("D "):
            reply = self._digest()
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
        self._relayout()
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        item = (_cost(word), len(word))
        last = self.lines[-1] if self.lines else None
        if last is not None and not last.items:
            last.items.append(item)
            last.dig = item[1]
        elif last is not None and last.fit + 1 + item[0] <= self.width:
            last.items.append(item)
            last.dig += 1 + item[1]
        else:
            self.lines.append(self._make_line([item]))
        self.doc.append(word)
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self) -> str:
        self.lines = []
        if not self.doc:
            self.lines.append(_Line())
        for i, word in enumerate(self.doc):
            if _cost(word) > self.width:
                word = word[:self.width]
                self.doc[i] = word
            cost, length = _cost(word), len(word)
            last = self.lines[-1] if self.lines else None
            if (last is not None and last.items and
                    last.fit + 1 + cost < self.width):
                last.items.append((cost, length))
                last.dig += length
            else:
                line = _Line()
                line.items.append((cost, length))
                line.dig = length
                self.lines.append(line)
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _relayout(self) -> None:
        """Re-wrap the last line at the current width."""
        if not self.lines or not self.lines[-1].items:
            return
        last = self.lines.pop()
        current: list[tuple[int, int]] = []
        for item in last.items:
            if current and self._fit(current) + 1 + item[0] > self.width:
                self.lines.append(self._make_line(current))
                current = [item]
            else:
                current.append(item)
        self.lines.append(self._make_line(current))

    @staticmethod
    def _fit(items: list[tuple[int, int]]) -> int:
        return sum(c for c, _ in items) + len(items) - 1

    @staticmethod
    def _make_line(items: list[tuple[int, int]]) -> _Line:
        line = _Line()
        line.items = list(items)
        line.dig = sum(length for _, length in items) + len(items) - 1
        return line

    def _digest(self) -> str:
        total = sum(line.dig * _WEIGHTS[i % 2] for i, line in enumerate(self.lines))
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
