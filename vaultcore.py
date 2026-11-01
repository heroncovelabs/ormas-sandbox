"""VaultCore versioned document vault, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads vault
commands on stdin (``W`` writes a document at a format version, ``G``
reads a document's digest, ``M`` bulk-migrates remaining v1 documents,
``C`` prints the vault checksum), writes one reply per command and an
``X`` trailer at EOF. Format reference: ``docs/SPEC.md`` (note the drift
warning at the top of that file; the legacy engine's behavior is the
contract).

Engine behavior that differs from the spec, reproduced here:

- The digest skips byte 0; weights cycle 4, 9 starting at byte 1.
- Doc ids are case-insensitive (replies echo the id as given).
- Tokens beyond the expected count are ignored; tokens are separated by
  spaces (runs of spaces collapse).
- Version downgrades are accepted and replace the document.
- The bulk sweep migrates by uppercasing, stripping trailing digits, and
  cutting a 20-character result to 18 characters. A lazy read only
  uppercases, unless the document is dirty (rewritten at v1 while still
  stored at v1), in which case it migrates exactly like the sweep.
"""

from __future__ import annotations

import sys

ID_MAX = 8
BODY_MAX = 20
DIGEST_MOD = 97
CHECKSUM_MOD = 1000000007
_WEIGHTS = (4, 9)
_SWEEP_CUT = 18


def digest(body: str) -> int:
    """Weighted byte sum of the stored body from byte 1, weights cycling 4, 9."""
    total = sum(ord(c) * _WEIGHTS[i % 2] for i, c in enumerate(body[1:]))
    return total % DIGEST_MOD


def migrate(body: str) -> str:
    """Lazy read-path migration of a clean v1 body."""
    return body.upper()


def sweep_migrate(body: str) -> str:
    """Bulk sweep migration (also used by reads of dirty documents)."""
    body = body.upper().rstrip("0123456789")
    if len(body) >= BODY_MAX:
        body = body[:_SWEEP_CUT]
    return body


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _valid_body(token: str) -> bool:
    return 1 <= len(token) <= BODY_MAX and token.isascii() and token.isalnum()


class Engine:
    """Document vault with lazy/bulk migration and batch counters."""

    def __init__(self) -> None:
        # folded doc id -> [version, body, dirty]
        self.docs: dict[str, list] = {}
        self.writes = 0
        self.reads = 0
        self.migrated = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        tokens = [t for t in line.split(" ") if t]
        if line == "W" or line.startswith("W "):
            reply = self._write(tokens)
            kind = "W"
        elif line == "G" or line.startswith("G "):
            reply = self._read(tokens)
            kind = "G"
        elif line == "M" or line.startswith("M "):
            reply = self._sweep(tokens)
            kind = "M"
        elif line == "C" or line.startswith("C "):
            reply = self._checksum(tokens)
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
        c1 = sum(1 for doc in self.docs.values() if doc[0] == 1)
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
        key = doc.lower()
        prev = self.docs.get(key)
        dirty = ver == 1 and prev is not None and prev[0] == 1
        self.docs[key] = [ver, body, dirty]
        c1, c2 = self._counts()
        return f"OK {c1} {c2}"

    def _read(self, tokens: list[str]) -> str:
        if len(tokens) < 2:
            return "R ???????? FMT"
        doc = tokens[1]
        if not _valid_id(doc):
            return "R ???????? FMT"
        key = doc.lower()
        if key not in self.docs:
            return "NIL"
        ver, body, dirty = self.docs[key]
        if ver == 1:
            body = sweep_migrate(body) if dirty else migrate(body)
            self.docs[key] = [2, body, False]
            self.migrated += 1
        return f"D {digest(body)}"

    def _sweep(self, tokens: list[str]) -> str:
        count = 0
        for key, (ver, body, _) in self.docs.items():
            if ver != 1:
                continue
            self.docs[key] = [2, sweep_migrate(body), False]
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
