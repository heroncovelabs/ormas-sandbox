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


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered
        self.allocated_keys = 0  # Deleted entries retain their legacy array slots.
        self.sessions: dict[bytes, int] = {}

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        # The daemon uses fgets with a 512-byte buffer and bounded sscanf fields.
        raw = rfile.readline(511)
        if not raw:
            return
        parts = _scan(_line(raw), (15, 0, 63))
        if (
            len(parts) != 3
            or parts[0] != b"HELLO"
            or not 1 <= parts[1] <= 9
            or not _alnum(parts[2], 1, 8)
        ):
            send(b"ERR HANDSHAKE")
            return
        negotiated = 3 if parts[1] >= 3 else 1
        node = parts[2]
        session = self.sessions.setdefault(node, len(self.sessions) + 1)
        send(f"WELCOME {negotiated} S{session}".encode())

        commands = 1  # Includes the handshake and every nonempty command line.
        for raw in iter(lambda: rfile.readline(511), b""):
            line = _line(raw)
            if not line:
                continue
            commands += 1
            parts = _scan(line, (15, 127, 127))
            cmd = parts[0] if parts else b""
            if cmd == b"BYE":
                send(f"GOODBYE {commands}".encode())
                return
            if cmd == b"PUT" and len(parts) >= 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= 64:
                key, value = parts[1], parts[2][:48]
                old = self.store.get(key)
                if old is None:
                    if self.allocated_keys >= MAX_KEYS:
                        send(b"ERR FULL")
                        continue
                    self.allocated_keys += 1
                self.store[key] = value
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
    # C strings end at NUL; the daemon also cuts at the first CR or LF.
    return re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]


def _scan(line: bytes, widths: tuple[int, ...]) -> list:
    """Read the daemon's sscanf fields; width zero denotes a signed C int."""
    fields = []
    pos = 0
    for width in widths:
        pattern = rb"\s*([+-]?[0-9]+)" if width == 0 else rb"\s*(\S{1,%d})" % width
        match = re.match(pattern, line[pos:])
        if match is None:
            break
        value = match[1]
        pos += match.end()
        if width == 0:
            # glibc scans through a saturated signed long, then narrows to int.
            number = max(-(1 << 63), min(int(value), (1 << 63) - 1))
            value = (number + (1 << 31)) % (1 << 32) - (1 << 31)
        fields.append(value)
    return fields


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
