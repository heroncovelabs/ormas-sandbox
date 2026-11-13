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
# Fold the engine actually uses for signatures re-imposed after an edit
# landed ahead of the persisted imposition: (p8,p7,p1,p2), (p6,p5,p3,p4).
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        # Persisted imposition: one entry (a list of sheets) per signature.
        self.cache: list[list[tuple[str, ...]]] | None = None
        self.dirty = 0  # first signature touched since the last impose
        self.patched = False  # an insert landed ahead of the tail
        self.changed = False  # document edited since the last impose
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        if line == "G" or line.startswith("G "):
            return self._impose()
        if line == "P" or line.startswith("P "):
            return [self._page(line.split())]
        if line == "I" or line.startswith("I "):
            return [self._insert(line.split())]
        return [self._reject("????????", "FMT")]

    def trailer(self) -> str:
        return f"X {self.pages} {self.inserts} {self.imposes} {self.rejected}"

    def _reject(self, page: str, code: str) -> str:
        self.rejected += 1
        return f"N {page} {code}"

    def _touch(self, pos: int) -> None:
        sig = pos // SIG_PAGES
        self.dirty = sig if not self.changed else min(self.dirty, sig)
        self.changed = True

    def _keys(self) -> list[str]:
        return [p.lower() for p in self.doc]

    def _page(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        page = tokens[1]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        if page.lower() in self._keys():
            return self._reject(page, "DUP")
        self._touch(len(self.doc))
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
        keys = self._keys()
        if front:
            ai = -1
        elif anchor.lower() in keys:
            ai = keys.index(anchor.lower())
        else:
            return self._reject(page, "WHERE")
        if page.lower() in keys:
            return self._reject(page, "DUP")
        self.patched = self.patched or front or ai + 1 < len(self.doc)
        self._touch(ai + 1)
        self.doc.insert(ai + 1, page)
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _fold_sig(self, s: int, fold=FOLD) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = [
            self.doc[base + i] if base + i < len(self.doc) else "-"
            for i in range(SIG_PAGES)
        ]
        sheets = [tuple(ent[i] for i in half) for half in fold]
        if len(self.doc) - base == 2:
            sheets.reverse()
        return sheets

    def _impose(self) -> list[str]:
        # The engine persists its imposition: an unchanged document
        # re-emits it, an edit ahead of the tail re-imposes from the first
        # edited signature with the patch fold (earlier signatures stay as
        # persisted), and anything else is folded afresh.
        nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
        if self.cache is None or (self.changed and not self.patched):
            self.cache = [self._fold_sig(s) for s in range(nsigs)]
        elif self.changed:
            self.cache = self.cache[: self.dirty] + [
                self._fold_sig(s, PATCH_FOLD) for s in range(self.dirty, nsigs)
            ]
        self.patched = False
        self.changed = False
        self.imposes += 1
        sheets = [sh for sig in self.cache for sh in sig]
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
