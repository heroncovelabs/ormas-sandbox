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
MAX_LINE_BYTES = 511  # The legacy fgets buffer holds 512 bytes including NUL.
STORED_VALUE_BYTES = 48


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered
        self.sessions: dict[bytes, int] = {}
        self.insertions = 0  # Deleted entries still consume legacy store slots.

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        raw = rfile.readline(MAX_LINE_BYTES)
        if not raw:
            return
        handshake = _handshake(_line(raw))
        if handshake is None:
            send(b"ERR HANDSHAKE")
            return
        version, node = handshake
        negotiated = 1 if version < 3 else 3
        if node not in self.sessions:
            self.sessions[node] = len(self.sessions) + 1
        send(f"WELCOME {negotiated} S{self.sessions[node]}".encode())

        commands = 1  # The handshake and BYE both contribute to GOODBYE.
        for raw in iter(lambda: rfile.readline(MAX_LINE_BYTES), b""):
            line = _line(raw)
            if not line:
                continue
            commands += 1
            parts = line.split()
            if not parts:
                send(b"ERR FMT")
                continue
            cmd = parts[0]
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


def _line(raw: bytes) -> bytes:
    # The C peer treats NUL and the first CR/LF as the end of the record.
    return re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]


def _handshake(line: bytes) -> tuple[int, bytes] | None:
    parts = line.split(None, 1)
    if len(parts) < 2 or parts[0] != b"HELLO":
        return None
    # scanf's decimal conversion may end immediately before the node token.
    number = re.match(rb"[+-]?[0-9]+", parts[1])
    if number is None:
        return None
    version = int(number[0])
    # Match the legacy signed-long conversion followed by a 32-bit int cast.
    version = max(-(1 << 63), min(version, (1 << 63) - 1))
    version = (version + (1 << 31)) % (1 << 32) - (1 << 31)
    nodes = parts[1][number.end():].split()
    if not 1 <= version <= 9 or not nodes or not _alnum(nodes[0], 1, 8):
        return None
    return version, nodes[0]


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
