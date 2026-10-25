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


def _fit_len(word: str) -> int:
    """Width a word occupies for the wrap test (digits do not count)."""
    return sum(1 for c in word if c.isalpha())


class Engine:
    """Layout engine mirroring the legacy binary's observable behaviour.

    Per line we keep three things: the words, ``fit`` (the width used by
    the wrap test) and ``lens`` (the length the digest weighs).
    """

    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[list[str]] = []
        self.fit: list[int] = []
        self.lens: list[int] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        tokens = line.split()
        cmd = tokens[0] if tokens else ""
        if cmd == "W":
            reply = self._width(tokens)
        elif cmd == "A":
            reply = self._append(tokens)
        elif cmd == "R":
            reply = self._reflow(tokens)
        elif cmd == "D":
            reply = self._digest(tokens)
        else:
            reply = "E FMT"
        if reply.startswith("E "):
            self.rejected += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.words} {self.reflows} {self.rejected}"

    def _place(self, word: str) -> None:
        """Incremental greedy placement of one word (joins if it fits)."""
        if self.lines and not self.lines[-1]:
            self.lines[-1].append(word)
            self.fit[-1] = _fit_len(word)
            self.lens[-1] = len(word)
        elif self.lines and self.fit[-1] + 1 + _fit_len(word) <= self.width:
            self.lines[-1].append(word)
            self.fit[-1] += 1 + _fit_len(word)
            self.lens[-1] += 1 + len(word)
        else:
            self.lines.append([word])
            self.fit.append(_fit_len(word))
            self.lens.append(len(word))

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
        # Changing the width re-lays only the current (last) line.
        if self.lines and self.lines[-1]:
            words = self.lines.pop()
            self.fit.pop()
            self.lens.pop()
            self.lines.append([words[0]])
            self.fit.append(_fit_len(words[0]))
            self.lens.append(len(words[0]))
            for word in words[1:]:
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
        # Legacy reflow clips stored words wider than the width (by their
        # wrap width, digits excluded) down to the width, permanently.
        self.doc = [w[:self.width] if _fit_len(w) > self.width else w
                    for w in self.doc]
        self.lines = []
        self.fit = []
        self.lens = []
        for word in self.doc:
            if self.lines and self.fit[-1] + 1 + _fit_len(word) < self.width:
                self.lines[-1].append(word)
                self.fit[-1] += 1 + _fit_len(word)
                self.lens[-1] += len(word)
            else:
                self.lines.append([word])
                self.fit.append(_fit_len(word))
                self.lens.append(len(word))
        if not self.lines:
            # An empty document still reports one (empty) line.
            self.lines = [[]]
            self.fit = [0]
            self.lens = [0]
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self, tokens: list[str]) -> str:
        total = sum(n * _WEIGHTS[i % 2] for i, n in enumerate(self.lens))
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
