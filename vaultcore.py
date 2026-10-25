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

import re
import sys

ID_MAX = 8
BODY_MAX = 20
DIGEST_MOD = 97
CHECKSUM_MOD = 1000000007
_WEIGHTS = (4, 9)
_TOKEN_SPLIT = re.compile(r" +")


def _tokens(line: str) -> list[str]:
    # The legacy parser stops each token at NUL, then at an ASCII space.
    tokens = _TOKEN_SPLIT.split(line.split("\x00", 1)[0])
    return [token for token in tokens if token]


def digest(body: str) -> int:
    """Legacy weighted byte sum; its digest loop starts at byte one."""
    total = sum(ord(c) * _WEIGHTS[(i - 1) % 2] for i, c in enumerate(body[1:], 1))
    return total % DIGEST_MOD


def migrate(body: str, dirty: bool = False, bulk: bool = False) -> str:
    """Apply the path-dependent legacy v1 migration transform."""
    if dirty or bulk:
        body = body.rstrip("0123456789")
        if len(body) == BODY_MAX:
            body = body[:18]
    return body.upper()


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _valid_body(token: str) -> bool:
    return 1 <= len(token) <= BODY_MAX and token.isascii() and token.isalnum()


class Engine:
    """Document vault with lazy/bulk migration and batch counters."""

    def __init__(self) -> None:
        # Uppercase doc id -> (version, body, dirty-v1 rewrite flag)
        self.docs: dict[str, tuple[int, str, bool]] = {}
        self.writes = 0
        self.reads = 0
        self.migrated = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        command = line.split("\x00", 1)[0]
        if command == "W" or command.startswith("W "):
            reply = self._write(_tokens(line))
            kind = "W"
        elif command == "G" or command.startswith("G "):
            reply = self._read(_tokens(line))
            kind = "G"
        elif command == "M" or command.startswith("M "):
            reply = self._sweep(_tokens(line))
            kind = "M"
        elif command == "C" or command.startswith("C "):
            reply = self._checksum(_tokens(line))
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
        c1 = sum(1 for ver, _, _ in self.docs.values() if ver == 1)
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
        ver = int(vtok)
        key = doc.upper()
        old = self.docs.get(key)
        dirty = ver == 1 and old is not None and old[0] == 1
        self.docs[key] = (ver, body, dirty)
        c1, c2 = self._counts()
        return f"OK {c1} {c2}"

    def _read(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "R ???????? FMT"
        doc = tokens[1]
        if not _valid_id(doc):
            return "R ???????? FMT"
        key = doc.upper()
        if key not in self.docs:
            return "NIL"
        ver, body, dirty = self.docs[key]
        if ver == 1:
            body = migrate(body, dirty)
            self.docs[key] = (2, body, False)
            self.migrated += 1
        return f"D {digest(body)}"

    def _sweep(self, tokens: list[str]) -> str:
        count = 0
        for doc, (ver, body, _) in list(self.docs.items()):
            if ver != 1:
                continue
            self.docs[doc] = (2, migrate(body, bulk=True), False)
            count += 1
        self.migrated += count
        return f"M {count}"

    def _checksum(self, tokens: list[str]) -> str:
        total = sum(digest(body) for _, body, _ in self.docs.values())
        return f"C {total % CHECKSUM_MOD}"


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    for raw in lines:
        # strcspn-style line trimming stops at the first CR or LF.
        line = raw.split("\r", 1)[0].split("\n", 1)[0]
        if not line:
            continue
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    # Latin-1 preserves arbitrary input bytes for legacy-style validation.
    lines = [raw.decode("latin-1") for raw in sys.stdin.buffer]
    process(lines, out=sys.stdout)


if __name__ == "__main__":
    main()
