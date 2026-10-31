"""FoldCore imposition engine, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads
imposition commands on stdin (``P`` appends a page, ``I`` inserts a page
after an anchor, ``G`` imposes the document onto sheets), writes one
reply (or sheet block) per command and an ``X`` trailer at EOF.
Format reference: ``docs/SPEC.md`` (note the drift warning at the top of
that file; the legacy engine's behavior is the contract).

Where the engine departs from the spec:

- A line ends at the first ``\\r``. The command letter must be followed
  by a space or the end of the line; tokens are separated by runs of
  spaces and extra trailing tokens are ignored (``G`` too).
- Page ids are compared case-insensitively (duplicates and anchors) but
  echoed exactly as given.
- A final signature holding exactly 2 pages is laid out as if two blank
  pages preceded them.
- Re-imposition: an unchanged document re-emits the cached layout; a
  document that only grew at the tail (appends, inserts after the last
  page) is imposed afresh with the documented fold; otherwise the
  signatures before the first changed page keep their cached sheets and
  every signature from there on uses the patch fold.
"""

from __future__ import annotations

import sys

ID_MAX = 8
SIG_PAGES = 8
# Documented fold: signature pages p1..p8 land on sheets
# (p8,p1,p2,p7) and (p6,p3,p4,p5); 0-based slot indices below.
FOLD = ((7, 0, 1, 6), (5, 2, 3, 4))
# Fold used when re-imposing after a mid-document edit:
# (p8,p7,p1,p2) and (p6,p5,p3,p4).
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))
# A final signature holding exactly this many pages gets two phantom
# blank slots at its front.
CREEP_PAGES = 2
CREEP_BLANKS = 2


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.keys: list[str] = []  # case-folded ids, parallel to doc
        self.cached_keys: list[str] | None = None  # document at last G
        self.cached_sigs: list[list[tuple[str, ...]]] = []
        self.edited = False  # mid-document insert since the last G
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        cmd = line[0]
        if cmd not in "PIG" or (len(line) > 1 and line[1] != " "):
            return [self._reject("????????", "FMT")]
        tokens = [t for t in line[1:].split(" ") if t]
        if cmd == "G":
            return self._impose()
        if cmd == "P":
            return [self._page(tokens)]
        return [self._insert(tokens)]

    def trailer(self) -> str:
        return f"X {self.pages} {self.inserts} {self.imposes} {self.rejected}"

    def _reject(self, page: str, code: str) -> str:
        self.rejected += 1
        return f"N {page} {code}"

    def _page(self, tokens: list[str]) -> str:
        if not tokens:
            return self._reject("????????", "FMT")
        page = tokens[0]
        if not _valid_id(page):
            return self._reject("????????", "FMT")
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        self.doc.append(page)
        self.keys.append(page.lower())
        self.pages += 1
        return f"OK {len(self.doc)}"

    def _insert(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return self._reject("????????", "FMT")
        page, anchor = tokens[0], tokens[1]
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
        if front or ai + 1 < len(self.doc):
            self.edited = True  # not an insert after the last page
        self.doc.insert(ai + 1, page)
        self.keys.insert(ai + 1, page.lower())
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _fold_sig(self, s: int, fold) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        count = min(SIG_PAGES, len(self.doc) - base)
        lead = CREEP_BLANKS if count == CREEP_PAGES else 0
        ent = ["-"] * lead + self.doc[base:base + count]
        ent += ["-"] * (SIG_PAGES - len(ent))
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
        old = self.cached_keys
        if old is not None and old == self.keys:
            sigs = self.cached_sigs
        elif old is None or not self.edited:
            sigs = [self._fold_sig(s, FOLD) for s in range(nsigs)]
        else:
            first = next(
                (i for i, (a, b) in enumerate(zip(old, self.keys)) if a != b),
                len(old),
            )
            keep = first // SIG_PAGES
            sigs = self.cached_sigs[:keep] + [
                self._fold_sig(s, PATCH_FOLD) for s in range(keep, nsigs)
            ]
        self.cached_keys = list(self.keys)
        self.cached_sigs = sigs
        self.edited = False
        self.imposes += 1
        sheets = [sheet for sig in sigs for sheet in sig]
        out = [f"SHEET {a} {b} {c} {d}" for a, b, c, d in sheets]
        out.append(f"GEND {len(sheets)}")
        return out


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies: list[str] = []
    for raw in lines:
        line = raw.rstrip("\n").split("\r", 1)[0]
        if not line:
            continue
        replies.extend(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    data = sys.stdin.buffer.read().decode("latin-1")
    process(data.split("\n"), out=sys.stdout)


if __name__ == "__main__":
    main()
