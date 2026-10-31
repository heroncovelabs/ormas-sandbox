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
        self.ids: dict[str, int] = {}
        self.sheets: list[tuple[str, ...]] | None = None
        self.dirty = False
        self.dirty_from: int | None = None
        self.patch = False
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        # The controller protocol separates tokens with literal spaces.
        tokens = [token for token in line.split(" ") if token]
        if line == "G" or line.startswith("G "):
            return self._impose()
        if line == "P" or line.startswith("P "):
            return [self._page(tokens)]
        if line == "I" or line.startswith("I "):
            return [self._insert(tokens)]
        return [self._reject("????????", "FMT")]

    def trailer(self) -> str:
        return f"X {self.pages} {self.inserts} {self.imposes} {self.rejected}"

    def _reject(self, page: str, code: str) -> str:
        self.rejected += 1
        return f"N {page} {code}"

    def _page(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        page = tokens[1]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        if page.lower() in self.ids:
            return self._reject(page, "DUP")
        self._changed(len(self.doc))
        self.ids[page.lower()] = len(self.doc)
        self.doc.append(page)
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
            ai = -1
        elif anchor.lower() in self.ids:
            ai = self.ids[anchor.lower()]
        else:
            return self._reject(page, "WHERE")
        if page.lower() in self.ids:
            return self._reject(page, "DUP")
        position = ai + 1
        self._changed(position, front or position < len(self.doc))
        self.doc.insert(position, page)
        for i in range(position, len(self.doc)):
            self.ids[self.doc[i].lower()] = i
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _changed(self, position: int, patch: bool = False) -> None:
        signature = position // SIG_PAGES
        self.dirty_from = (signature if self.dirty_from is None
                           else min(self.dirty_from, signature))
        self.patch |= patch and self.sheets is not None
        self.dirty = True

    def _fold_sig(self, s: int, patch: bool = False) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = self.doc[base:base + SIG_PAGES]
        # A two-page final signature carries two leading creep blanks.
        if len(ent) == 2:
            ent = ["-", "-"] + ent
        ent += ["-"] * (SIG_PAGES - len(ent))
        fold = PATCH_FOLD if patch else FOLD
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        if self.sheets is None or self.dirty:
            nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
            if not self.patch:
                # Appends alone rebuild the whole layout in the ordinary fold.
                sheets: list[tuple[str, ...]] = []
                start = 0
            else:
                # All edits share the earliest pending signature watermark;
                # previously printed sheets before it retain their exact fold.
                start = self.dirty_from
                sheets = self.sheets[:2 * start]
            for s in range(start, nsigs):
                sheets.extend(self._fold_sig(s, self.patch))
            self.sheets = sheets
            self.dirty = False
            self.dirty_from = None
            self.patch = False
        self.imposes += 1
        out = [f"SHEET {a} {b} {c} {d}" for a, b, c, d in self.sheets]
        out.append(f"GEND {len(self.sheets)}")
        return out


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies: list[str] = []
    for raw in lines:
        # The original line reader terminates C strings at CR, LF, or NUL.
        line = raw.split("\0", 1)[0].split("\r", 1)[0].split("\n", 1)[0]
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
