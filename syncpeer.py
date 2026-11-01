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
MAX_LINE = 511  # Payload size of the legacy peer's fgets buffer.
MAX_VALUE = 48


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered
        self.insertions = 0  # Deleted entries still consume legacy storage slots.
        self.sessions: dict[bytes, int] = {}

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        raw = rfile.readline(MAX_LINE)
        if not raw:
            return
        # sscanf's decimal conversion can leave a node immediately after the
        # version (e.g. HELLO 3node), and ignores tokens after the node.
        line = _line(raw)
        hello = re.match(rb"\s*HELLO\s+([+-]?[0-9]+)", line)
        nodes = line[hello.end():].split() if hello else []
        version = _version(hello[1]) if hello else 0
        if not 1 <= version <= 9 or not nodes or not _alnum(nodes[0], 1, 8):
            send(b"ERR HANDSHAKE")
            return
        node = nodes[0]
        session = self.sessions.setdefault(node, len(self.sessions) + 1)
        negotiated = 3 if version >= 3 else 1
        send(f"WELCOME {negotiated} S{session}".encode())

        commands = 1  # The handshake and BYE both contribute to the count.
        for raw in iter(lambda: rfile.readline(MAX_LINE), b""):
            line = _line(raw)
            if not line:
                continue
            commands += 1
            parts = line.split()
            cmd = parts[0] if parts else b""
            if cmd == b"BYE":
                send(f"GOODBYE {commands}".encode())
                return
            if (
                cmd == b"PUT"
                and len(parts) >= 3
                and _alnum(parts[1], 1, 16)
                and 1 <= len(parts[2]) <= 64
            ):
                key, value = parts[1], parts[2][:MAX_VALUE]
                previous = self.store.get(key)
                if previous is None:
                    if self.insertions >= MAX_KEYS:
                        send(b"ERR FULL")
                        continue
                    self.insertions += 1
                self.store[key] = value
                if previous is not None and previous != value:
                    send(b"OK " + previous)
                else:
                    send(b"OK")
            elif cmd == b"GET" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                value = self.store.get(parts[1])
                missing = b"ERR NOTFOUND" if negotiated == 3 else b"NIL"
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
    # C strings end at NUL; strcspn strips at the first CR or LF.
    return re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]


def _version(token: bytes) -> int:
    # The legacy scanf converts through a signed long, then stores an int.
    number = max(-(1 << 63), min(int(token), (1 << 63) - 1))
    return (number + (1 << 31)) % (1 << 32) - (1 << 31)


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
