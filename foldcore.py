"""FoldCore imposition engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
imposition commands on stdin (``P`` appends a page, ``I`` inserts a page
after an anchor, ``G`` imposes the document onto sheets), writes one
reply (or sheet block) per command and an ``X`` trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).
"""

from __future__ import annotations

import sys

ID_MAX = 8
SIG_PAGES = 8
# Documented fold: signature pages p1..p8 land on sheets
# (p8,p1,p2,p7) and (p6,p3,p4,p5); 0-based slot indices below.
FOLD = ((7, 0, 1, 6), (5, 2, 3, 4))
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.ids: set[str] = set()  # ASCII case-insensitive identity
        self.sheets: list[tuple[str, ...]] = []
        self.imposed = False
        self.dirty = False
        self.dirty_from: int | None = None
        self.patch = False
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        if line == "G" or line.startswith("G "):
            return self._impose()
        if line == "P" or line.startswith("P "):
            return [self._page([token for token in line.split(" ") if token])]
        if line == "I" or line.startswith("I "):
            return [self._insert([token for token in line.split(" ") if token])]
        return [self._reject("????????", "FMT")]

    def trailer(self) -> str:
        return f"X {self.pages} {self.inserts} {self.imposes} {self.rejected}"

    def _reject(self, page: str, code: str) -> str:
        self.rejected += 1
        return f"N {page} {code}"

    def _changed(self, index: int, interior: bool = False) -> None:
        signature = index // SIG_PAGES
        if self.dirty_from is None:
            self.dirty_from = signature
        else:
            self.dirty_from = min(self.dirty_from, signature)
        self.dirty = True
        self.patch |= interior

    def _page(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        page = tokens[1]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        if page.lower() in self.ids:
            return self._reject(page, "DUP")
        self._changed(len(self.doc))
        self.doc.append(page)
        self.ids.add(page.lower())
        self.pages += 1
        return f"OK {len(self.doc)}"

    def _insert(self, tokens: list[str]) -> str:
        if len(tokens) < 3:
            return self._reject("????????", "FMT")
        page, anchor = tokens[1], tokens[2]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        front = anchor == "0"  # '0' is always the document front
        if not front and not _valid_id(anchor):
            return self._reject(page, "FMT")
        if front:
            index = 0
        elif anchor.lower() in self.ids:
            index = next(i + 1 for i, p in enumerate(self.doc)
                         if p.lower() == anchor.lower())
        else:
            return self._reject(page, "WHERE")
        if page.lower() in self.ids:
            return self._reject(page, "DUP")
        self._changed(index, interior=front or index < len(self.doc))
        self.doc.insert(index, page)
        self.ids.add(page.lower())
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _fold_sig(self, s: int, patch: bool = False) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = self.doc[base:base + SIG_PAGES]
        # A two-page final signature carries a pair of leading blank leaves.
        if len(ent) == 2:
            ent = ["-", "-"] + ent
        ent += ["-"] * (SIG_PAGES - len(ent))
        fold = PATCH_FOLD if patch else FOLD
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        if self.dirty or not self.imposed:
            nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
            start = self.dirty_from if self.imposed else 0
            patch = self.imposed and self.patch
            self.sheets = self.sheets[:start * 2]
            for s in range(start, nsigs):
                self.sheets.extend(self._fold_sig(s, patch))
            # Patch passes retain the earliest edit boundary. The next ordinary
            # rebuild consumes it, including when a tail append triggers that G.
            if not patch:
                self.dirty_from = None
            self.imposed = True
            self.dirty = False
            self.patch = False
        self.imposes += 1
        out = [f"SHEET {a} {b} {c} {d}" for a, b, c, d in self.sheets]
        out.append(f"GEND {len(self.sheets)}")
        return out


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies: list[str] = []
    for raw in lines:
        # The legacy line scanner stops at CR, LF, or the C-string terminator;
        # command fields are separated exclusively by literal spaces.
        line = raw.split("\r", 1)[0].split("\n", 1)[0].split("\0", 1)[0]
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    lines = [raw.decode("utf-8", errors="surrogateescape")
             for raw in sys.stdin.buffer.readlines()]
    process(lines, out=sys.stdout)


if __name__ == "__main__":
    main()
