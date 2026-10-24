"""ReflowCore greedy word-wrap layout engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
layout commands on stdin (``W`` sets the wrap width, ``A`` appends a word
with incremental layout, ``R`` reflows the whole document, ``D`` prints
the layout digest), writes one reply per command and an ``X`` trailer at
EOF. Format reference: ``docs/SPEC.md`` (note the drift warning at the
top of that file; the legacy engine's behavior is the contract).

Legacy behaviors reproduced here (where the spec is wrong or silent):

- Extra tokens after a command's required fields are ignored.
- Digits occupy no width when fitting words onto a line (letters only),
  but every character counts toward the digest.
- ``A`` accepts words wider than the current width (they start their own
  line); ``R`` later truncates any word whose fit width exceeds the wrap
  width to its first ``width`` characters, permanently.
- ``R`` joins a word only if ``current + 1 + word < width`` (strict), and
  the reflowed lines' stored lengths omit the joining spaces.
- ``R`` on an empty document yields one empty line.
- ``W`` re-lays the LAST line's words at the new width with the append
  rule (it may split, never merges with earlier lines), recomputing its
  lengths including the joining spaces; earlier lines are untouched.
- Commands are split on spaces only (a tab is not a separator).
- The document holds at most 8192 words; a valid ``A`` beyond that is
  rejected ``FMT``.
"""

from __future__ import annotations

import sys

WORD_MAX = 16
WIDTH_MIN = 10
WIDTH_MAX = 120
DIGEST_MOD = 1000003
DOC_MAX = 8192
_WEIGHTS = (3, 5)


def _valid_word(token: str) -> bool:
    return 1 <= len(token) <= WORD_MAX and token.isascii() and token.isalnum()


def _fit(word: str) -> int:
    """Width a word occupies when fitting: digits take no room."""
    return sum(1 for c in word if not c.isdigit())


class Line:
    __slots__ = ("words", "dlen", "flen")

    def __init__(self, words: list[str], dlen: int, flen: int) -> None:
        self.words = words
        self.dlen = dlen  # length used by the digest
        self.flen = flen  # length used when fitting further words

    @classmethod
    def spaced(cls, words: list[str]) -> "Line":
        n = len(words) - 1 if words else 0
        return cls(words, sum(len(w) for w in words) + n,
                   sum(_fit(w) for w in words) + n)


class Engine:
    def __init__(self) -> None:
        self.width = 40
        self.doc: list[str] = []
        self.lines: list[Line] = []
        self.words = 0
        self.reflows = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # the engine splits on spaces only; tabs are part of a token
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

    def _wrap(self, words: list[str]) -> list[Line]:
        """Incremental greedy rule applied to a run of words."""
        out: list[Line] = []
        for word in words:
            self._place(out, word)
        return out

    def _place(self, lines: list[Line], word: str) -> None:
        if lines and not lines[-1].words:
            last = lines[-1]
            last.words.append(word)
            last.dlen = len(word)
            last.flen = _fit(word)
        elif lines and lines[-1].flen + 1 + _fit(word) <= self.width:
            last = lines[-1]
            last.words.append(word)
            last.dlen += 1 + len(word)
            last.flen += 1 + _fit(word)
        else:
            lines.append(Line([word], len(word), _fit(word)))

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
            self.lines.extend(self._wrap(last.words))
        return "OK"

    def _append(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "E FMT"
        word = tokens[1]
        if not _valid_word(word):
            return "E WORD"
        if len(self.doc) >= DOC_MAX:
            return "E FMT"  # the engine's document buffer is full
        self.doc.append(word)
        self._place(self.lines, word)
        self.words += 1
        return f"L {len(self.lines)}"

    def _reflow(self, tokens: list[str]) -> str:
        self.doc = [w[:self.width] if _fit(w) > self.width else w
                    for w in self.doc]
        lines: list[Line] = []
        cur = 0
        for word in self.doc:
            if lines and cur + 1 + _fit(word) < self.width:
                lines[-1].words.append(word)
                cur += 1 + _fit(word)
            else:
                lines.append(Line([word], 0, 0))
                cur = _fit(word)
        for line in lines:
            line.dlen = sum(len(w) for w in line.words)
            line.flen = sum(_fit(w) for w in line.words) + len(line.words) - 1
        if not lines:
            lines.append(Line([], 0, 0))
        self.lines = lines
        self.reflows += 1
        return f"L {len(self.lines)}"

    def _digest(self, tokens: list[str]) -> str:
        total = sum(line.dlen * _WEIGHTS[i % 2]
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
