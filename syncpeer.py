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
LINE_BYTES = 511  # fgets() reserves one byte of its 512-byte buffer for NUL.
VALUE_BYTES = 48


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered
        self.insertions = 0  # Deleted entries still consume a legacy store slot.
        self.sessions: dict[bytes, int] = {}
        self.next_session = 1

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        raw = rfile.readline(LINE_BYTES)
        if not raw:
            return
        handshake = _handshake(_line(raw))
        if handshake is None:
            send(b"ERR HANDSHAKE")
            return
        offered, node = handshake
        negotiated = 1 if offered < 3 else 3
        session = self.sessions.setdefault(node, len(self.sessions) + 1)
        send(f"WELCOME {negotiated} S{session}".encode())

        commands = 1  # The successful handshake is included in the count.
        for raw in iter(lambda: rfile.readline(LINE_BYTES), b""):
            line = _line(raw)
            if not line:
                continue
            commands += 1
            parts = _tokens(line, (15, 127, 127))
            cmd = parts[0] if parts else b""
            if cmd == b"BYE":
                send(f"GOODBYE {commands}".encode())
                return
            if cmd == b"PUT" and len(parts) == 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= 64:
                old = self.store.get(parts[1])
                if old is None:
                    if self.insertions >= MAX_KEYS:
                        send(b"ERR FULL")
                        continue
                    self.insertions += 1
                value = parts[2][:VALUE_BYTES]
                self.store[parts[1]] = value
                send(b"OK " + old if old is not None and old != value else b"OK")
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


def _line(raw: bytes) -> bytes:
    # C strings end at NUL; the daemon also discards the first CR/LF onward.
    return re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]


def _tokens(line: bytes, widths: tuple[int, ...]) -> list[bytes]:
    """Read the bounded %s fields used by the daemon's command scanner."""
    parts = []
    position = 0
    for width in widths:
        field = re.match(rb"\s*(\S{1," + str(width).encode() + rb"})", line[position:])
        if field is None:
            break
        parts.append(field[1])
        position += field.end()
    return parts


def _handshake(line: bytes) -> tuple[int, bytes] | None:
    command = re.match(rb"\s*(\S{1,15})", line)
    if command is None or command[1] != b"HELLO":
        return None
    version = re.match(rb"\s*([+-]?[0-9]+)", line[command.end():])
    if version is None:
        return None
    node = _tokens(line[command.end() + version.end():], (63,))
    # Match the legacy %d conversion: saturate strtol, then narrow to int32.
    number = max(-(1 << 63), min(int(version[1]), (1 << 63) - 1))
    number = (number + (1 << 31)) % (1 << 32) - (1 << 31)
    if not 1 <= number <= 9 or not node or not _alnum(node[0], 1, 8):
        return None
    return number, node[0]


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
