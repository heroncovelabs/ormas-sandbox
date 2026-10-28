"""SyncPeer replication peer, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). A TCP
server on 127.0.0.1 (ephemeral port by default, printed as
``LISTENING <port>``), serving one client at a time; the key-value store
lives for the whole process. Protocol reference: ``docs/SPEC.md`` (mind
the drift warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import argparse
import socket
import sys

MAX_KEYS = 4096
MAX_SESSIONS = 1024


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # active keys in slot order
        self.slots = 0
        self.sessions: dict[str, int] = {}

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line) -> None:
            if isinstance(line, str):
                line = line.encode()
            wfile.write(line + b"\n")
            wfile.flush()

        raw = _readline(rfile)
        if raw is None:
            return
        parts = _tokens(raw)
        if (
            len(parts) < 3
            or parts[0] != b"HELLO"
            or not 1 <= _version(parts[1]) <= 9
            or not _alnum(parts[2], 1, 8)
        ):
            send("ERR HANDSHAKE")
            return
        requested = _version(parts[1])
        negotiated = min(requested, 3) if requested != 2 else 1
        node = parts[2].decode()
        if node not in self.sessions and len(self.sessions) >= MAX_SESSIONS:
            send("ERR HANDSHAKE")
            return
        session = self.sessions.setdefault(node, len(self.sessions) + 1)
        send(f"WELCOME {negotiated} S{session}")

        commands = 1
        for raw in iter(lambda: _readline(rfile), None):
            line = raw.rstrip(b"\r\n")
            if not line:
                continue
            commands += 1
            parts = _tokens(line)
            if not parts:
                send("ERR FMT")
                continue
            cmd = parts[0]
            if cmd == b"BYE":
                send(f"GOODBYE {commands}")
                return
            if cmd == b"PUT" and len(parts) >= 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= 64:
                key = parts[1]
                value = parts[2][:48]
                if key not in self.store and self.slots >= MAX_KEYS:
                    send("ERR FULL")
                    continue
                previous = self.store.get(key)
                if previous is None:
                    self.slots += 1
                self.store[key] = value
                send(b"OK " + previous if previous is not None and previous != value else "OK")
            elif cmd == b"GET" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                value = self.store.get(parts[1])
                if value is not None:
                    send(b"VAL " + value)
                else:
                    send("NIL" if negotiated == 1 else "ERR NOTFOUND")
            elif cmd == b"DEL" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                if parts[1] in self.store:
                    del self.store[parts[1]]
                    send("OK")
                else:
                    send("ERR NOTFOUND")
            elif cmd == b"KEYS" and len(parts) >= 2 and len(parts[1]) <= 16:
                prefix = _lower(parts[1])
                matches = [
                    key for key in reversed(self.store)
                    if _lower(key).startswith(prefix)
                ]
                for key in matches:
                    send(b"KEY " + key)
                send(f"END {len(matches)}")
            else:
                send("ERR FMT")

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


def _readline(rfile):
    line = rfile.readline(511)
    return line if line else None


def _tokens(line: bytes) -> list[bytes]:
    return line.split(b"\0", 1)[0].split()


def _version(value: bytes) -> int:
    digits = value[1:] if value.startswith(b"+") else value
    return int(digits) if digits.isdigit() and digits.isascii() else -1


def _alnum(value: bytes, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and value.isalnum() and value.isascii()


def _lower(value: bytes) -> bytes:
    return value.translate(bytes.maketrans(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ", b"abcdefghijklmnopqrstuvwxyz"))


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
