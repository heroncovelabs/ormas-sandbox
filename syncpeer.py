"""SyncPeer replication peer, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). A TCP
server on 127.0.0.1 (ephemeral port by default, printed as
``LISTENING <port>``), serving one client at a time; the key-value store
lives for the whole process. Protocol reference: ``docs/SPEC.md`` (mind
the drift warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import argparse
import re
import socket
import sys

MAX_KEYS = 4096
MAX_SESSIONS = 1024
MAX_LINE_BYTES = 511  # fgets uses a 512-byte buffer, including its terminator.
STORED_VALUE_BYTES = 48
_WHITESPACE = b" \t\n\r\v\f"
_DECIMAL = re.compile(rb"[+-]?[0-9]+")


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered, case-sensitive
        self.insertions = 0  # Deleted entries still occupy a legacy store slot.
        self.sessions: dict[bytes, int] = {}
        self.session_serial = 0

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        raw = rfile.readline(MAX_LINE_BYTES)
        if not raw:
            return
        handshake = _handshake(_wire_line(raw))
        if handshake is None:
            send(b"ERR HANDSHAKE")
            return
        version, node = handshake
        negotiated = 1 if version == 2 else min(version, 3)
        session = self.sessions.get(node)
        if session is None:
            self.session_serial += 1
            session = self.session_serial
            # Once the registry fills, fresh nodes receive an uncached token.
            if len(self.sessions) < MAX_SESSIONS:
                self.sessions[node] = session
        send(f"WELCOME {negotiated} S{session}".encode())

        commands = 1  # The handshake and BYE both contribute to GOODBYE.
        for raw in iter(lambda: rfile.readline(MAX_LINE_BYTES), b""):
            line = _wire_line(raw)
            if not line:
                continue
            commands += 1
            parts = _words(line, (15, 127, 127))
            cmd = parts[0] if parts else b""
            if cmd == b"BYE":
                send(f"GOODBYE {commands}".encode())
                return
            if cmd == b"PUT" and len(parts) >= 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= 64:
                key, value = parts[1], parts[2][:STORED_VALUE_BYTES]
                previous = self.store.get(key)
                if previous is None:
                    if self.insertions >= MAX_KEYS:
                        send(b"ERR FULL")
                        continue
                    self.insertions += 1
                self.store[key] = value
                send(b"OK " + previous if previous is not None and previous != value else b"OK")
            elif cmd == b"GET" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                value = self.store.get(parts[1])
                missing = b"NIL" if negotiated == 1 else b"ERR NOTFOUND"
                send(b"VAL " + value if value is not None else missing)
            elif cmd == b"DEL" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                if parts[1] in self.store:
                    del self.store[parts[1]]
                    send(b"OK")
                else:
                    send(b"ERR NOTFOUND")
            elif cmd == b"KEYS" and len(parts) >= 2 and len(parts[1]) <= 16:
                prefix = parts[1].lower()
                matches = [k for k in reversed(self.store) if k.lower().startswith(prefix)]
                for key in matches:
                    send(b"KEY " + key)
                send(f"END {len(matches)}".encode())
            else:
                send(b"ERR FMT")

    # -- accept loop --------------------------------------------------------

    def run(self, port: int) -> None:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(8)
        print(f"LISTENING {listener.getsockname()[1]}", flush=True)
        while True:
            conn, _ = listener.accept()
            with conn:
                rfile = conn.makefile("rb")
                wfile = conn.makefile("wb")
                try:
                    self.serve_connection(rfile, wfile)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    rfile.close()
                    try:
                        wfile.close()
                    except (BrokenPipeError, ConnectionResetError):
                        pass


def _wire_line(raw: bytes) -> bytes:
    # The daemon treats input as a C string, ending at its first NUL, CR or LF.
    return raw.partition(b"\0")[0].partition(b"\r")[0].partition(b"\n")[0]


def _word(line: bytes, start: int, width: int) -> tuple[bytes, int]:
    while start < len(line) and line[start] in _WHITESPACE:
        start += 1
    end = start
    limit = min(len(line), start + width)
    while end < limit and line[end] not in _WHITESPACE:
        end += 1
    return line[start:end], end


def _words(line: bytes, widths: tuple[int, ...]) -> list[bytes]:
    # sscanf's field widths can split a long token across consecutive fields.
    parts = []
    start = 0
    for width in widths:
        word, start = _word(line, start, width)
        if not word:
            break
        parts.append(word)
    return parts


def _handshake(line: bytes) -> tuple[int, bytes] | None:
    command, start = _word(line, 0, 15)
    if command != b"HELLO":
        return None
    tail = line[start:].lstrip(_WHITESPACE)
    number = _DECIMAL.match(tail)
    if number is None:
        return None
    # The legacy %d conversion consumes a signed decimal prefix via strtol,
    # saturates at a signed 64-bit long, then narrows to a 32-bit integer.
    version = max(-(1 << 63), min((1 << 63) - 1, int(number[0]))) & 0xFFFFFFFF
    node, _ = _word(tail, number.end(), 63)
    if not 1 <= version <= 9 or not _alnum(node, 1, 8):
        return None
    return version, node


def _alnum(value: bytes, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and value.isalnum()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    try:
        Peer().run(args.port)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
