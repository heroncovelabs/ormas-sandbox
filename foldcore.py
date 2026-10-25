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
# Fold the engine uses for signatures at or after an insert point.
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0
        self.imposed = False
        self.laid = 0  # pages in the last layout
        self.cache: list[str] | None = None  # last emitted layout
        self.edited = False  # mid-document insert since the last layout
        self.mark = None  # first signature touched by a mid-document insert

    def _find(self, page: str) -> int:
        key = page.lower()
        for i, p in enumerate(self.doc):
            if p.lower() == key:
                return i
        return -1

    def handle(self, line: str) -> list[str]:
        tokens = line.split()
        cmd = tokens[0] if tokens else ""
        if cmd == "G":
            return self._impose()
        if cmd == "P":
            return [self._page(tokens)]
        if cmd == "I":
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
        if self._find(page) >= 0:
            return self._reject(page, "DUP")
        self.doc.append(page)
        self.cache = None
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
        elif self._find(anchor) >= 0:
            ai = self._find(anchor)
        else:
            return self._reject(page, "WHERE")
        if self._find(page) >= 0:
            return self._reject(page, "DUP")
        self.doc.insert(ai + 1, page)
        if self.imposed and (ai < 0 or ai + 2 < len(self.doc)):
            sig = (ai + 1) // SIG_PAGES
            if self.laid % SIG_PAGES:
                sig = min(sig, (self.laid - 1) // SIG_PAGES)
            if self.mark is None or sig < self.mark:
                self.mark = sig
            self.edited = True
        self.cache = None
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _fold_sig(self, s: int) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        pages = self.doc[base:base + SIG_PAGES]
        ent = [pages[i] if i < len(pages) else "-" for i in range(SIG_PAGES)]
        fold = PATCH_FOLD if self.mark is not None and s >= self.mark else FOLD
        sheets = [tuple(ent[i] for i in half) for half in fold]
        if len(pages) == 2:
            sheets.reverse()
        return sheets

    def _impose(self) -> list[str]:
        # The engine persists the imposition: an unchanged document
        # re-emits the stored layout.  After edits the layout is
        # recomputed; signatures from the first mid-document insert on
        # use the patch fold, and that watermark survives until a layout
        # is pulled with no mid-document insert since the previous one.
        self.imposes += 1
        self.imposed = True
        if self.cache is not None:
            return list(self.cache)
        if not self.edited:
            self.mark = None
        nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
        sheets: list[tuple[str, ...]] = []
        for s in range(nsigs):
            sheets.extend(self._fold_sig(s))
        self.edited = False
        self.laid = len(self.doc)
        out = [f"SHEET {a} {b} {c} {d}" for a, b, c, d in sheets]
        out.append(f"GEND {len(sheets)}")
        self.cache = out
        return list(out)


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies: list[str] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    process(sys.stdin.readlines(), out=sys.stdout)


if __name__ == "__main__":
    main()
