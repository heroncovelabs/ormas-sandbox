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
# Rebuilding an imposed suffix uses the engine's patch traversal.
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.ids: dict[str, str] = {}
        self.sheets: list[tuple[str, ...]] | None = None
        self.dirty_from: int | None = None
        self.patch = False
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        # The protocol separates tokens with literal spaces. Extra fields
        # are ignored, and tabs remain part of a token for validation.
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
        self._edited(len(self.doc))
        self.doc.append(page)
        self.ids[page.lower()] = page
        self.pages += 1
        return f"OK {len(self.doc)}"

    def _insert(self, tokens: list[str]) -> str:
        if len(tokens) < 3:
            return self._reject("????????", "FMT")
        page, anchor = tokens[1:3]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        front = anchor == "0"  # '0' is always the document front
        if not front and not _valid_id(anchor):
            return self._reject(page, "FMT")
        if front:
            ai = -1
        elif anchor.lower() in self.ids:
            ai = self.doc.index(self.ids[anchor.lower()])
        else:
            return self._reject(page, "WHERE")
        if page.lower() in self.ids:
            return self._reject(page, "DUP")
        pos = ai + 1
        # The front sentinel always selects the insertion path, including
        # insertion into an empty document that has already been imposed.
        self._edited(pos, patch=front or pos < len(self.doc))
        self.doc.insert(pos, page)
        self.ids[page.lower()] = page
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _edited(self, pos: int, patch: bool = False) -> None:
        signature = pos // SIG_PAGES
        if self.dirty_from is None or signature < self.dirty_from:
            self.dirty_from = signature
        # Appends contribute to the shared watermark; an interior insert
        # selects patch folding for the whole dirty suffix.
        if self.sheets is not None and patch:
            self.patch = True

    def _fold_sig(self, s: int, patch: bool = False) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = self.doc[base:base + SIG_PAGES]
        # A two-page tail carries two leading blank leaves. This padding
        # is local to the layout and never becomes part of the document.
        if len(ent) == 2:
            ent = ["-", "-"] + ent
        ent += ["-"] * (SIG_PAGES - len(ent))
        fold = PATCH_FOLD if patch else FOLD
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        if self.sheets is None or self.dirty_from is not None:
            nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
            sheets: list[tuple[str, ...]] = []
            for s in range(nsigs):
                patch = self.patch and s >= self.dirty_from
                if (self.patch and not patch
                        and self.sheets is not None and 2 * s < len(self.sheets)):
                    sheets.extend(self.sheets[2 * s:2 * s + 2])
                else:
                    sheets.extend(self._fold_sig(s, patch))
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
        # The legacy line reader terminates commands at LF, CR, or NUL.
        line = raw.split("\n", 1)[0].split("\r", 1)[0].split("\0", 1)[0]
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Keep embedded CR in its physical LF-delimited input line.
    lines = sys.stdin.buffer.read().decode("utf-8", errors="surrogateescape").split("\n")
    process(lines, out=sys.stdout)


if __name__ == "__main__":
    main()
