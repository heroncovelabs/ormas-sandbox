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
# Engine behavior: once a page has been slotted into an already-imposed
# document, signatures from the one holding that insert onward are laid
# out with this patch fold instead.
PATCH_FOLD = ((7, 6, 0, 1), (5, 4, 2, 3))


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


class Engine:
    """Imposition engine with append/insert, sheet cache, and counters."""

    def __init__(self) -> None:
        self.doc: list[str] = []  # page ids in document order
        self.keys: list[str] = []  # case-folded ids, parallel to doc
        self.pages = 0
        self.inserts = 0
        self.imposes = 0
        self.rejected = 0
        # Persisted layout: per-signature sheet pairs from the last G, or
        # None before the first G.
        self.sigs: list[list[tuple[str, ...]]] | None = None
        self.dirty_sig = 0  # first signature changed since the last G
        self.changed = False  # document changed since the last G
        # A page was slotted into the imposed document (not after its last
        # page) since the last G, so the next G patches the layout.
        self.patching = False

    def handle(self, line: str) -> list[str]:
        # Engine behavior: runs of spaces separate tokens and trailing
        # tokens are ignored.
        cmd = line.split(" ")[0]
        tokens = [cmd] + [t for t in line[len(cmd):].split(" ") if t]
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
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        self._touch(len(self.doc))
        self.doc.append(page)
        self.keys.append(page.lower())
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
            ai = self.keys.index(anchor.lower())
        else:
            return self._reject(page, "WHERE")
        if page.lower() in self.keys:
            return self._reject(page, "DUP")
        pos = ai + 1
        # Slotting in after the last page is an append as far as the fold
        # is concerned; anything else after a proof patches the layout.
        if self.sigs is not None and (front or pos < len(self.doc)):
            self.patching = True
        self._touch(pos)
        self.doc.insert(pos, page)
        self.keys.insert(pos, page.lower())
        self.inserts += 1
        return f"OK {len(self.doc)}"

    def _touch(self, pos: int) -> None:
        self.dirty_sig = min(self.dirty_sig, pos // SIG_PAGES)
        self.changed = True

    def _fold_sig(self, s: int, last: bool, patched: bool) -> list[tuple[str, ...]]:
        base = s * SIG_PAGES
        ent = self.doc[base:base + SIG_PAGES]
        # Engine behavior: a final signature holding exactly two pages
        # starts with a pair of blank slots.
        if last and len(ent) == 2:
            ent = ["-", "-"] + ent
        ent = ent + ["-"] * (SIG_PAGES - len(ent))
        fold = PATCH_FOLD if patched else FOLD
        return [tuple(ent[i] for i in half) for half in fold]

    def _impose(self) -> list[str]:
        # Engine behavior: when pages were slotted into the persisted
        # layout, it is patched rather than rebuilt. Signatures ahead of the
        # first one touched since the last G keep their cached sheets
        # (whatever fold produced them); the rest get the patch fold.
        # Without such inserts the layout is rebuilt with the documented
        # fold (or re-emitted as is when nothing changed).
        self.imposes += 1
        nsigs = (len(self.doc) + SIG_PAGES - 1) // SIG_PAGES
        if self.sigs is None:
            keep = 0
        elif self.patching:
            keep = min(self.dirty_sig, len(self.sigs))
        elif not self.changed:
            keep = nsigs
        else:
            keep = 0
        sigs = [] if self.sigs is None else self.sigs[:keep]
        for s in range(keep, nsigs):
            sigs.append(self._fold_sig(s, s == nsigs - 1, self.patching))
        self.sigs = sigs
        self.dirty_sig = nsigs
        self.changed = False
        self.patching = False  # only inserts since the last G patch
        sheets = [sheet for sig in sigs for sheet in sig]
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
