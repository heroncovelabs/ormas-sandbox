"""VaultCore versioned document vault, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads vault
commands on stdin (``W`` writes a document at a format version, ``G``
reads a document's digest, ``M`` bulk-migrates remaining v1 documents,
``C`` prints the vault checksum), writes one reply per command and an
``X`` trailer at EOF. Format reference: ``docs/SPEC.md`` (note the drift
warning at the top of that file; the legacy engine's behavior is the
contract).
"""

from __future__ import annotations

import sys

ID_MAX = 8
BODY_MAX = 20
DIGEST_MOD = 97
CHECKSUM_MOD = 1000000007
_WEIGHTS = (4, 9)


def _weight(index: int) -> int:
    """Byte 0 weighs 0; later bytes cycle 4, 9 starting at byte 1."""
    if index == 0:
        return 0
    return _WEIGHTS[(index - 1) % 2]


def digest(body: str) -> int:
    """Weighted byte sum of the stored body, modulo 97."""
    total = sum(ord(c) * _weight(i) for i, c in enumerate(body))
    return total % DIGEST_MOD


def migrate(body: str, *, compact: bool = False) -> str:
    """Uppercase v1 content, applying the sweep/dirty-rewrite compaction."""
    body = body.upper()
    if compact:
        body = body.rstrip("0123456789")
        # The legacy compactor drops two bytes when its output fills the buffer.
        if len(body) == BODY_MAX:
            body = body[:-2]
    return body


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _valid_body(token: str) -> bool:
    return 1 <= len(token) <= BODY_MAX and token.isascii() and token.isalnum()


def _fold(doc: str) -> str:
    """Document identity is case-insensitive."""
    return doc.upper()


def _tokenize(line: str) -> list[str]:
    """Tokens are separated by single spaces only; empty fields are skipped."""
    return [token for token in line.split(" ") if token]


class Engine:
    """Document vault with lazy/bulk migration and batch counters."""

    def __init__(self) -> None:
        # folded doc id -> (version, body)
        self.docs: dict[str, tuple[int, str]] = {}
        # A write over an unmigrated v1 document selects the compacting reader.
        self.dirty: set[str] = set()
        self.writes = 0
        self.reads = 0
        self.migrated = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        if line == "W" or line.startswith("W "):
            reply = self._write(_tokenize(line))
            kind = "W"
        elif line == "G" or line.startswith("G "):
            reply = self._read(_tokenize(line))
            kind = "G"
        elif line == "M" or line.startswith("M "):
            reply = self._sweep(_tokenize(line))
            kind = "M"
        elif line == "C" or line.startswith("C "):
            reply = self._checksum(_tokenize(line))
            kind = "C"
        else:
            reply = "R ???????? FMT"
            kind = "?"
        if reply.startswith("R "):
            self.rejected += 1
        elif kind == "W":
            self.writes += 1
        elif kind == "G":
            self.reads += 1
        return reply

    def trailer(self) -> str:
        return f"X {self.writes} {self.reads} {self.migrated} {self.rejected}"

    def _counts(self) -> tuple[int, int]:
        c1 = sum(1 for ver, _ in self.docs.values() if ver == 1)
        return c1, len(self.docs) - c1

    def _write(self, tokens: list[str]) -> str:
        if len(tokens) < 4:
            return "R ???????? FMT"
        doc, vtok, body = tokens[1], tokens[2], tokens[3]
        if not _valid_id(doc):
            return "R ???????? FMT"
        if vtok not in ("1", "2"):
            return f"R {doc} VER"
        if not _valid_body(body):
            return f"R {doc} BODY"
        key = _fold(doc)
        ver = int(vtok)
        if ver == 1 and key in self.docs and self.docs[key][0] == 1:
            self.dirty.add(key)
        else:
            self.dirty.discard(key)
        self.docs[key] = (ver, body)
        c1, c2 = self._counts()
        return f"OK {c1} {c2}"

    def _read(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "R ???????? FMT"
        doc = tokens[1]
        if not _valid_id(doc):
            return "R ???????? FMT"
        key = _fold(doc)
        if key not in self.docs:
            return "NIL"
        ver, body = self.docs[key]
        if ver == 1:
            body = migrate(body, compact=key in self.dirty)
            self.docs[key] = (2, body)
            self.dirty.discard(key)
            self.migrated += 1
        return f"D {digest(body)}"

    def _sweep(self, tokens: list[str]) -> str:
        count = 0
        for doc, (ver, body) in self.docs.items():
            if ver != 1:
                continue
            self.docs[doc] = (2, migrate(body, compact=True))
            self.dirty.discard(doc)
            count += 1
        self.migrated += count
        return f"M {count}"

    def _checksum(self, tokens: list[str]) -> str:
        total = sum(digest(body) for _, body in self.docs.values())
        return f"C {total % CHECKSUM_MOD}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    process(sys.stdin.readlines(), out=sys.stdout)


if __name__ == "__main__":
    main()
