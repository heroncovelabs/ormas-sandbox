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
# Engine patch fold: once a page has been slotted into an imposed job,
# every signature from the first one the insert touched onward folds as
# (p8,p7,p1,p2) and (p6,p5,p3,p4) instead.
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.keys: set[str] = set()  # case-folded ids (engine ids are case-insensitive)
        # Persisted imposition: per-signature sheet pairs from the last G
        # (None before the first G), plus what changed since that G.
        self.cache: list[list[tuple[str, ...]]] | None = None
        self.dirty_from: int | None = None  # lowest doc index changed since last G
        self.patched = False  # a mid-document insert happened since last G
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0

    def handle(self, line: str) -> list[str]:
        # The engine ignores stray trailing tokens on every command and
        # separates tokens by runs of spaces only (a tab is part of a token).
        tokens = [t for t in line.split(" ") if t]
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
        elif anchor.lower() in self.keys:
            low = anchor.lower()
            ai = next(i for i, p in enumerate(self.doc) if p.lower() == low)
        else:
            return self._reject(page, "WHERE")
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        pos = ai + 1
        # Inserting after the last page behaves exactly like an append; a
        # front insert always patches, even into an empty document.
        self._touch(pos, front or pos < len(self.doc))
        self.doc.insert(pos, page)
        self.keys.add(page.lower())
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _touch(self, pos: int, mid: bool) -> None:
        if self.dirty_from is None or pos < self.dirty_from:
            self.dirty_from = pos
        self.patched = self.patched or mid

    def _fold_sig(self, s: int, last: bool, fold) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = [
            self.doc[base + i] if base + i < len(self.doc) else "-"
            for i in range(SIG_PAGES)
        ]
        if last and len(self.doc) % SIG_PAGES == 2:
            # Engine creep: a 2-page final signature starts 2 slots in.
            ent = ["-", "-"] + ent[:-2]
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        # Engine re-imposition: an unchanged document re-emits the cache;
        # appends alone recompute everything with the documented fold; a
        # mid-document insert keeps cached signatures ahead of the lowest
        # change since the last G and patch-folds everything from there.
        nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
        if self.cache is not None and self.dirty_from is None:
            keep, fold = len(self.cache), FOLD
        elif self.cache is None or not self.patched:
            keep, fold = 0, FOLD
        else:
            keep, fold = self.dirty_from // SIG_PAGES, PATCH_FOLD
        sigs = self.cache[:keep] if self.cache is not None else []
        for s in range(keep, nsigs):
            sigs.append(self._fold_sig(s, s == nsigs - 1, fold))
        self.cache = sigs
        self.dirty_from = None
        self.patched = False
        sheets = [sheet for sig in sigs for sheet in sig]
        self.imposes += 1
        out = [f"SHEET {a} {b} {c} {d}" for a, b, c, d in sheets]
        out.append(f"GEND {len(sheets)}")
        return out


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies: list[str] = []
    for raw in lines:
        # The engine ends each line at the first CR or NUL as well as LF.
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
    # Read raw bytes: text mode would treat a lone CR as a line break.
    data = sys.stdin.buffer.read().decode("latin-1")
    process(data.split("\n"), out=sys.stdout)


if __name__ == "__main__":
    main()
