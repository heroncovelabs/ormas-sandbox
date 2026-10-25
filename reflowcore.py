"""Behavioral replacement for the retired ReflowCore layout engine.

The command format is described in ``docs/SPEC.md``.  The production
engine is authoritative where that document has drifted; the layout and
accounting quirks below are intentional compatibility behavior.
"""

from __future__ import annotations

import sys

WORD_MAX = 16
DOC_MAX = 8192
WIDTH_MIN = 10
WIDTH_MAX = 120
DIGEST_MOD = 1000003
_WEIGHTS = (3, 5)


def _valid_word(token: str) -> bool:
    return 1 <= len(token) <= WORD_MAX and token.isascii() and token.isalnum()


def _alpha_len(word: str) -> int:
    return sum("A" <= char <= "Z" or "a" <= char <= "z" for char in word)


class Engine:
    """Stateful command processor compatible with the retired engine."""

    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        # Inclusive document-index spans [start, end) define each line.
        self.lines: list[tuple[int, int]] = []
        self.line_lengths: list[int] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
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

    def _fit_len(self, line_index: int) -> int:
        start, end = self.lines[line_index]
        if start == end:
            return 0
        return (end - start - 1
                + sum(_alpha_len(self.doc[i]) for i in range(start, end)))

    def _width(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        value = tokens[1]
        if not (2 <= len(value) <= 3 and value.isascii() and value.isdigit()):
            return "E WIDTH"
        width = int(value)
        if not WIDTH_MIN <= width <= WIDTH_MAX:
            return "E WIDTH"
        self.width = width
        if self.lines:
            start, end = self.lines.pop()
            self.line_lengths.pop()
            if start < end:
                self.lines.append((start, start + 1))
                self.line_lengths.append(len(self.doc[start]))
            for index in range(start + 1, end):
                word = self.doc[index]
                fit = self._fit_len(len(self.lines) - 1)
                if fit + 1 + _alpha_len(word) <= width:
                    line_start, _ = self.lines[-1]
                    self.lines[-1] = (line_start, index + 1)
                    self.line_lengths[-1] += len(word) + 1
                else:
                    self.lines.append((index, index + 1))
                    self.line_lengths.append(len(word))
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        if len(self.doc) >= DOC_MAX:
            return "E FMT"
        index = len(self.doc)
        self.doc.append(word)
        self.words += 1
        if self.lines:
            fit = self._fit_len(len(self.lines) - 1)
            start, end = self.lines[-1]
            if start != end and fit + 1 + _alpha_len(word) <= self.width:
                self.lines[-1] = (start, index + 1)
                self.line_lengths[-1] += len(word) + 1
            elif start == end:
                self.lines[-1] = (index, index + 1)
                self.line_lengths[-1] += len(word)
            else:
                self.lines.append((index, index + 1))
                self.line_lengths.append(len(word))
        else:
            self.lines.append((index, index + 1))
            self.line_lengths.append(len(word))
        return f"L {len(self.lines)}"

    def _reflow(self, tokens: list[str]) -> str:
        # The retired engine modifies the document during its truncation
        # pass, so later reflows see the shortened words as well.
        for i, word in enumerate(self.doc):
            if _alpha_len(word) > self.width:
                self.doc[i] = word[:self.width]
        self.lines = []
        self.line_lengths = []
        current_length = 0
        for index, word in enumerate(self.doc):
            fit_length = _alpha_len(word)
            if self.lines and current_length + 1 + fit_length < self.width:
                start, _ = self.lines[-1]
                self.lines[-1] = (start, index + 1)
                current_length += 1 + fit_length
                self.line_lengths[-1] += len(word)
            else:
                self.lines.append((index, index + 1))
                self.line_lengths.append(len(word))
                current_length = fit_length
        if not self.lines:
            self.lines = [(0, 0)]
            self.line_lengths = [0]
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self, tokens: list[str]) -> str:
        total = sum(length * _WEIGHTS[i % 2]
                    for i, length in enumerate(self.line_lengths))
        return f"D {total % DIGEST_MOD}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
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
    # TextIOWrapper normalizes bare carriage returns; the engine treats
    # them as terminators within the current input record instead.
    process(sys.stdin.buffer.read().decode("utf-8").split("\n"), out=sys.stdout)


if __name__ == "__main__":
    main()
