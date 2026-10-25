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
# Late interior inserts rebuild the affected suffix using this patch fold.
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _split(line: str) -> tuple[str, list[str]]:
    """Command word (raw first field) and non-empty argument fields.

    The engine splits on the space character only: tabs are not
    separators, runs of spaces are ignored, and arguments beyond those
    a command needs are ignored rather than rejected.
    """
    fields = line.split(" ")
    return fields[0], [f for f in fields[1:] if f]


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0
        self.sheets: list[tuple[str, ...]] | None = None
        self.dirty_from: int | None = None
        self.patch = False

    def _changed(self, index: int, patch: bool = False) -> None:
        signature = index // SIG_PAGES
        if self.dirty_from is None or signature < self.dirty_from:
            self.dirty_from = signature
        self.patch = self.patch or patch

    def handle(self, line: str) -> list[str]:
        cmd, args = _split(line)
        if cmd == "G":
            return self._impose()
        if cmd == "P":
            return [self._page(args)]
        if cmd == "I":
            return [self._insert(args)]
        return [self._reject("????????", "FMT")]

    def trailer(self) -> str:
        return f"X {self.pages} {self.inserts} {self.imposes} {self.rejected}"

    def _reject(self, page: str, code: str) -> str:
        self.rejected += 1
        return f"N {page} {code}"

    def _find(self, page: str) -> int:
        """Index of the page with this id, ignoring ASCII case; -1 if absent."""
        key = page.lower()
        for i, existing in enumerate(self.doc):
            if existing.lower() == key:
                return i
        return -1

    def _page(self, args: list[str]) -> str:
        if len(args) < 1:
            return self._reject("????????", "FMT")
        page = args[0]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        if self._find(page) >= 0:
            return self._reject(page, "DUP")
        self._changed(len(self.doc))
        self.doc.append(page)
        self.pages += 1
        return f"OK {len(self.doc)}"

    def _insert(self, args: list[str]) -> str:
        if len(args) < 2:
            return self._reject("????????", "FMT")
        page, anchor = args[0], args[1]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        front = anchor == "0"  # '0' is always the document front
        if not front and not _valid_id(anchor):
            return self._reject(page, "FMT")
        if front:
            ai = -1
        else:
            ai = self._find(anchor)
            if ai < 0:
                return self._reject(page, "WHERE")
        if self._find(page) >= 0:
            return self._reject(page, "DUP")
        index = ai + 1
        # The explicit front anchor uses the insert path even on an empty
        # document. An ordinary anchor at the tail uses the append path.
        self._changed(index, patch=front or index < len(self.doc))
        self.doc.insert(index, page)
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _fold_sig(self, s: int, patch: bool = False) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = self.doc[base:base + SIG_PAGES]
        # A two-page final signature has two leading creep blanks, in
        # addition to the usual trailing padding, under either fold.
        if len(ent) == 2:
            ent = ["-", "-"] + ent
        ent += ["-"] * (SIG_PAGES - len(ent))
        fold = PATCH_FOLD if patch else FOLD
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        if self.sheets is None or self.dirty_from is not None:
            patch = self.sheets is not None and self.patch
            # All edits since the last G share a watermark, including
            # appends. Patch rebuilds retain the cached prefix; an ordinary
            # rebuild lays out the entire document with the normal fold.
            start = self.dirty_from if patch else 0
            sheets = self.sheets[:start * 2] if patch else []
            nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
            for s in range(start, nsigs):
                sheets.extend(self._fold_sig(s, patch=patch))
            self.sheets = sheets
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
