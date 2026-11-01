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
# Patch fold: signatures re-imposed after a mid-document insert land on
# (p8,p7,p1,p2) and (p6,p5,p3,p4).
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.keys: set[str] = set()  # case-folded page ids
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0
        self.imposed = False  # a layout has been pulled
        # first signature folded with PATCH_FOLD (None: none patched)
        self.watermark: int | None = None
        # lowest signature touched since the last G, and whether any of
        # those edits was a mid-document insert
        self.dirty: int | None = None
        self.mid = False

    def handle(self, line: str) -> list[str]:
        # The command letter must open the line; tokens are separated by
        # runs of spaces only, and extra trailing tokens are ignored.
        if len(line) > 1 and line[1] != " ":
            return [self._reject("????????", "FMT")]
        tokens = [t for t in line.split(" ") if t]
        if line[0] == "G":
            return self._impose()
        if line[0] == "P":
            return [self._page(tokens)]
        if line[0] == "I":
            return [self._insert(tokens)]
        return [self._reject("????????", "FMT")]

    def trailer(self) -> str:
        return f"X {self.pages} {self.inserts} {self.imposes} {self.rejected}"

    def _reject(self, page: str, code: str) -> str:
        self.rejected += 1
        return f"N {page} {code}"

    def _index(self, page: str) -> int:
        key = page.lower()
        for i, p in enumerate(self.doc):
            if p.lower() == key:
                return i
        return -1

    def _page(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        page = tokens[1]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        self._touch(len(self.doc), False)
        self.doc.append(page)
        self.keys.add(page.lower())
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
        else:
            ai = self._index(anchor)
            if ai < 0:
                return self._reject(page, "WHERE")
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        pos = ai + 1
        # only an insert after the current last page counts as an append
        self._touch(pos, front or pos < len(self.doc))
        self.doc.insert(pos, page)
        self.keys.add(page.lower())
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _touch(self, pos: int, mid: bool) -> None:
        sig = pos // SIG_PAGES
        if self.dirty is None or sig < self.dirty:
            self.dirty = sig
        self.mid = self.mid or mid

    def _fold_sig(self, s: int, last: bool) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = [
            self.doc[base + i] if base + i < len(self.doc) else "-"
            for i in range(SIG_PAGES)
        ]
        if last and len(self.doc) - base == 2:
            ent = ["-", "-"] + ent[:6]
        fold = FOLD
        if self.watermark is not None and s >= self.watermark:
            fold = PATCH_FOLD
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        # The engine patches its persisted layout: after a mid-document
        # insert, signatures from the lowest one touched since the last
        # G onward are refolded with PATCH_FOLD (earlier ones keep their
        # cached fold); edits that only extend the tail refold everything
        # with the documented FOLD.
        if self.dirty is not None:
            if not self.imposed or not self.mid:
                self.watermark = None
            elif self.watermark is None or self.dirty < self.watermark:
                self.watermark = self.dirty
        self.dirty = None
        self.mid = False
        nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
        sheets: list[tuple[str, ...]] = []
        for s in range(nsigs):
            sheets.extend(self._fold_sig(s, s == nsigs - 1))
        self.imposes += 1
        self.imposed = True
        out = [f"SHEET {a} {b} {c} {d}" for a, b, c, d in sheets]
        out.append(f"GEND {len(sheets)}")
        return out


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
