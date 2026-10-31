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


def digest(body: str) -> int:
    """Weighted byte sum of the stored body, weights cycling 4, 9.

    Engine: byte 0 is skipped; the weights start at byte 1."""
    total = sum(ord(c) * _WEIGHTS[i % 2] for i, c in enumerate(body[1:]))
    return total % DIGEST_MOD


def migrate(body: str) -> str:
    """Migrate a v1 body to v2 on the lazy read path."""
    return body.upper()


def sweep_migrate(body: str) -> str:
    """Migrate a v1 body on the bulk sweep path (also used when reading a
    v1 document that was rewritten in place at v1).

    Engine: trailing digits are stripped, a body still at the 20-byte
    maximum is cut to 18 bytes, then the result is uppercased."""
    body = body.rstrip("0123456789")
    if len(body) >= BODY_MAX:
        body = body[:BODY_MAX - 2]
    return body.upper()


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _valid_body(token: str) -> bool:
    return 1 <= len(token) <= BODY_MAX and token.isascii() and token.isalnum()


class Engine:
    """Document vault with lazy/bulk migration and batch counters."""

    def __init__(self) -> None:
        # folded doc id -> (version, body)
        self.docs: dict[str, tuple[int, str]] = {}
        # folded doc ids rewritten in place at v1 while still stored at v1
        self.dirty: set[str] = set()
        self.writes = 0
        self.reads = 0
        self.migrated = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        # Engine: tokens are separated by runs of spaces (only spaces);
        # surplus trailing tokens are ignored.
        tokens = [t for t in line.split(" ") if t]
        cmd = line[0] if len(line) == 1 or line[1:2] == " " else ""
        if cmd == "W":
            reply = self._write(tokens)
            kind = "W"
        elif cmd == "G":
            reply = self._read(tokens)
            kind = "G"
        elif cmd == "M":
            reply = self._sweep(tokens)
            kind = "M"
        elif cmd == "C":
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
        ver = int(vtok)
        key = doc.upper()  # Engine: doc ids are case-insensitive
        # Engine: downgrades are accepted and replace in place.
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
        key = doc.upper()
        if key not in self.docs:
            return "NIL"
        ver, body = self.docs[key]
        if ver == 1:
            if key in self.dirty:
                body = sweep_migrate(body)
                self.dirty.discard(key)
            else:
                body = migrate(body)
            self.docs[key] = (2, body)
            self.migrated += 1
        return f"D {digest(body)}"

    def _sweep(self, tokens: list[str]) -> str:
        count = 0
        for key, (ver, body) in self.docs.items():
            if ver != 1:
                continue
            self.docs[key] = (2, sweep_migrate(body))
            count += 1
        self.dirty.clear()
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
