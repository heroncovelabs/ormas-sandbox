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
# Engine behavior: once a page has been inserted after an imposition,
# every signature from the one holding that page onward is laid out with
# the patch fold (p8,p7,p1,p2) and (p6,p5,p3,p4).
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.keys: set[str] = set()  # case-folded ids (engine ignores case)
        self.imposed = False  # at least one G so far
        self.patch_sig: int | None = None  # first signature on patch fold
        self.changed = False  # document edited since the last G
        self.patched = False  # patching insert since the last G
        self.layout: list[str] = []  # cached reply of the last G
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        if line == "G" or line.startswith("G "):
            return self._impose()
        # Tokens are separated by runs of spaces only (tabs stay in-token).
        if line == "P" or line.startswith("P "):
            return [self._page([t for t in line.split(" ") if t])]
        if line == "I" or line.startswith("I "):
            return [self._insert([t for t in line.split(" ") if t])]
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
        # Engine ignores stray trailing tokens.
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        page = tokens[1]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        self.doc.append(page)
        self.keys.add(page.lower())
        self.changed = True
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
        # An insert after the last page behaves as an append.
        if self.imposed and not (ai >= 0 and pos == len(self.doc)):
            sig = pos // SIG_PAGES
            if self.patch_sig is None or sig < self.patch_sig:
                self.patch_sig = sig
            self.patched = True
        self.doc.insert(pos, page)
        self.keys.add(page.lower())
        self.changed = True
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _fold_sig(self, s: int) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = self.doc[base:base + SIG_PAGES]
        # Engine quirk: a final signature holding exactly two pages
        # carries a blank pair ahead of them.
        if len(ent) == 2:
            ent = ["-", "-"] + ent
        ent = ent + ["-"] * (SIG_PAGES - len(ent))
        fold = FOLD
        if self.patch_sig is not None and s >= self.patch_sig:
            fold = PATCH_FOLD
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        self.imposes += 1
        if self.imposed and not self.changed:
            # Unchanged document: re-emit the persisted imposition.
            return list(self.layout)
        if not self.patched:
            # Only appends since the last G: a fresh documented-fold
            # imposition that drops any earlier patch watermark.
            self.patch_sig = None
        nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
        sheets: list[tuple[str, ...]] = []
        for s in range(nsigs):
            sheets.extend(self._fold_sig(s))
        self.imposed = True
        self.changed = False
        self.patched = False
        out = [f"SHEET {a} {b} {c} {d}" for a, b, c, d in sheets]
        out.append(f"GEND {len(sheets)}")
        self.layout = out
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
