"""VaultCore versioned document vault, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). Reads vault
commands on stdin (``W`` writes a document at a format version, ``G``
reads a document's digest, ``M`` bulk-migrates remaining v1 documents,
``C`` prints the vault checksum), writes one reply per command and an
``X`` trailer at EOF. Format reference: ``docs/SPEC.md`` (note the drift
warning at the top of that file; the legacy engine's behavior is the
contract).

Engine behaviors that differ from the spec (reproduced here):

- Input is read in ``fgets`` chunks of at most 65535 bytes; each chunk is
  cut at the first CR, LF or NUL, and an empty result is skipped.
- Tokens are separated by spaces only; extra trailing tokens are ignored.
- Doc ids are case-insensitive (folded to lowercase for storage); reject
  replies echo the id as given.
- Version downgrades are accepted and replace the document.
- The digest skips byte 0: weights cycle 4, 9 starting at byte 1.
- The bulk sweep migration uppercases, strips trailing digits, and cuts a
  20-character result to 18 characters. Lazy reads only uppercase, except
  for a "dirty" document (a v1 write over a stored v1 document), which a
  read migrates with the sweep transform.
"""

from __future__ import annotations

import sys

ID_MAX = 8
BODY_MAX = 20
DIGEST_MOD = 97
CHECKSUM_MOD = 1000000007
LINE_CHUNK = 65535  # fgets buffer of 65536 bytes
_WEIGHTS = (4, 9)


def digest(body: str) -> int:
    """Weighted byte sum of the stored body from byte 1 on, weights
    cycling 4, 9 (byte 0 is not counted)."""
    total = sum(ord(c) * _WEIGHTS[i % 2] for i, c in enumerate(body[1:]))
    return total % DIGEST_MOD


def migrate(body: str) -> str:
    """Lazy-read migration of a clean v1 body to v2."""
    return body.upper()


def sweep_migrate(body: str) -> str:
    """Bulk-sweep migration (also used by reads of dirty documents)."""
    out = body.upper().rstrip("0123456789")
    if len(out) == BODY_MAX:
        out = out[:BODY_MAX - 2]
    return out


def _valid_id(token: str) -> bool:
    return 1 <= len(token) <= ID_MAX and token.isascii() and token.isalnum()


def _valid_body(token: str) -> bool:
    return 1 <= len(token) <= BODY_MAX and token.isascii() and token.isalnum()


def _tokens(line: str) -> list[str]:
    return [t for t in line.split(" ") if t]


class Engine:
    """Document vault with lazy/bulk migration and batch counters."""

    def __init__(self) -> None:
        # folded doc id -> (version, body, dirty)
        self.docs: dict[str, tuple[int, str, bool]] = {}
        self.writes = 0
        self.reads = 0
        self.migrated = 0
        self.rejected = 0

    def handle(self, line: str) -> str:
        if line == "W" or line.startswith("W "):
            reply = self._write(_tokens(line))
            kind = "W"
        elif line == "G" or line.startswith("G "):
            reply = self._read(_tokens(line))
            kind = "G"
        elif line == "M" or line.startswith("M "):
            reply = self._sweep()
            kind = "M"
        elif line == "C" or line.startswith("C "):
            reply = self._checksum()
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
        key = doc.lower()
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
        key = doc.lower()
        if key not in self.docs:
            return "NIL"
        ver, body, dirty = self.docs[key]
        if ver == 1:
            body = sweep_migrate(body) if dirty else migrate(body)
            self.docs[key] = (2, body, False)
            self.migrated += 1
        return f"D {digest(body)}"

    def _sweep(self) -> str:
        count = 0
        for key, (ver, body, _) in self.docs.items():
            if ver != 1:
                continue
            self.docs[key] = (2, sweep_migrate(body), False)
            count += 1
        self.migrated += count
        return f"M {count}"

    def _checksum(self) -> str:
        total = sum(digest(body) for _, body, _ in self.docs.values())
        return f"C {total % CHECKSUM_MOD}"


def _commands(data: bytes):
    """Yield command lines the way the engine's fgets loop sees them."""
    pos = 0
    while pos < len(data):
        end = data.find(b"\n", pos)
        end = len(data) if end < 0 else end + 1
        for start in range(pos, end, LINE_CHUNK):
            chunk = data[start:min(start + LINE_CHUNK, end)]
            for stop in (b"\0", b"\r", b"\n"):
                cut = chunk.find(stop)
                if cut >= 0:
                    chunk = chunk[:cut]
            if chunk:
                yield chunk.decode("latin-1")
        pos = end


def process(lines: list[str], out=None) -> list[str]:
    engine = Engine()
    replies = []
    data = "".join(
        line if line.endswith("\n") else line + "\n" for line in lines
    ).encode("latin-1")
    for line in _commands(data):
        replies.append(engine.handle(line))
    replies.append(engine.trailer())
    if out is not None:
        for reply in replies:
            print(reply, file=out)
    return replies


def main() -> None:
    engine = Engine()
    out = sys.stdout
    for line in _commands(sys.stdin.buffer.read()):
        out.write(engine.handle(line) + "\n")
    out.write(engine.trailer() + "\n")


if __name__ == "__main__":
    main()
