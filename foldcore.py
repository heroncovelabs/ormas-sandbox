"""FoldCore imposition engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
imposition commands on stdin (``P`` appends a page, ``I`` inserts a page
after an anchor, ``G`` imposes the document onto sheets), writes one
reply (or sheet block) per command and an ``X`` trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Where the legacy engine differs from the spec:

- Commands are split on single spaces; tokens past the ones a command
  needs are ignored, and ``G`` accepts trailing tokens.
- Page ids compare case-insensitively (DUP and anchor lookup) but are
  echoed exactly as given.
- Once the document has been imposed, an insert that does not land after
  the last page patches the imposition: at the next G, signatures from
  the first one edited since the previous G (appends included) onward fold
  with ``PATCH_FOLD`` instead of ``FOLD``. The watermark only moves down
  while each changed re-imposition follows such an insert; a changed
  re-imposition without one folds everything with ``FOLD`` again.
- A final signature holding exactly two pages emits its sheets swapped.
- Lines end at the first NUL, CR or LF; lines empty after that are skipped.
"""

from __future__ import annotations

import sys

ID_MAX = 8
SIG_PAGES = 8
# Documented fold: signature pages p1..p8 land on sheets
# (p8,p1,p2,p7) and (p6,p3,p4,p5); 0-based slot indices below.
FOLD = ((7, 0, 1, 6), (5, 2, 3, 4))
# Fold used for patched signatures (p8,p7,p1,p2) and (p6,p5,p3,p4).
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.keys: list[str] = []  # case-folded page ids, parallel to doc
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0
        self.imposed = False
        self.patch_from: int | None = None  # first patched signature
        self.dirty_from: int | None = None  # first signature edited since G
        self.inserted = False  # mid-document insert since the last G
        self.layout: list[str] = []  # last imposed reply lines

    def handle(self, line: str) -> list[str]:
        if line == "G" or line.startswith("G "):
            return self._impose()
        if line.startswith("P "):
            return [self._page(line.split(" "))]
        if line.startswith("I "):
            return [self._insert(line.split(" "))]
        return [self._reject("????????", "FMT")]

    def trailer(self) -> str:
        return f"X {self.pages} {self.inserts} {self.imposes} {self.rejected}"

    def _reject(self, page: str, code: str) -> str:
        self.rejected += 1
        return f"N {page} {code}"

    def _page(self, tokens: list[str]) -> str:
        tokens = [t for t in tokens if t]
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        page = tokens[1]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        self._touch(len(self.doc) // SIG_PAGES)
        self.doc.append(page)
        self.keys.append(page.lower())
        self.pages += 1
        return f"OK {len(self.doc)}"

    def _insert(self, tokens: list[str]) -> str:
        tokens = [t for t in tokens if t]
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
        elif anchor.lower() in self.keys:
            ai = self.keys.index(anchor.lower())
        else:
            return self._reject(page, "WHERE")
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        pos = ai + 1
        sig = pos // SIG_PAGES
        self._touch(sig)
        if self.imposed and (front or ai < len(self.doc) - 1):
            self.inserted = True
        self.doc.insert(pos, page)
        self.keys.insert(pos, page.lower())
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _touch(self, sig: int) -> None:
        if self.dirty_from is None or sig < self.dirty_from:
            self.dirty_from = sig

    def _fold_sig(self, s: int) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = [
            self.doc[base + i] if base + i < len(self.doc) else "-"
            for i in range(SIG_PAGES)
        ]
        patched = self.patch_from is not None and s >= self.patch_from
        sheets = [tuple(ent[i] for i in half) for half in (PATCH_FOLD if patched else FOLD)]
        if len(self.doc) - base == 2:
            sheets.reverse()
        return sheets

    def _impose(self) -> list[str]:
        # The imposition persists: an unchanged document re-emits the
        # cached layout. A changed one is refolded. After a mid-document
        # insert, the patch watermark drops to the first signature edited
        # since the last G; a re-imposition without one clears it.
        self.imposes += 1
        if self.imposed and self.dirty_from is None:
            return list(self.layout)
        if not self.inserted:
            self.patch_from = None
        elif self.patch_from is None or self.dirty_from < self.patch_from:
            self.patch_from = self.dirty_from
        nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
        sheets: list[tuple[str, ...]] = []
        for s in range(nsigs):
            sheets.extend(self._fold_sig(s))
        self.imposed = True
        self.dirty_from = None
        self.inserted = False
        out = [f"SHEET {a} {b} {c} {d}" for a, b, c, d in sheets]
        out.append(f"GEND {len(sheets)}")
        self.layout = out
        return list(out)


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies: list[str] = []
    for raw in lines:
        # The engine ends a line at its first NUL, CR or LF and skips it
        # if that leaves nothing.
        line = raw.split("\0", 1)[0].split("\n", 1)[0].split("\r", 1)[0]
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Read raw bytes: universal-newline text mode would split lines at a
    # bare CR, which the engine does not do.
    data = sys.stdin.buffer.read().decode("latin-1")
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    process(lines, out=sys.stdout)


if __name__ == "__main__":
    main()
