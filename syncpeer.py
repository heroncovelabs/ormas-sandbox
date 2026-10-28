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
_VERSION = re.compile(br"[+-]?[0-9]+")


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered
        self.connections = 0
        self.sessions: dict[bytes, int] = {}
        self.slots = 0

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        self.connections += 1
        raw = rfile.readline(511)
        if not raw:
            return
        handshake = _parse_handshake(raw.split(b"\0", 1)[0])
        if handshake is None:
            send(b"ERR HANDSHAKE")
            return
        version, node = handshake
        if node not in self.sessions:
            self.sessions[node] = len(self.sessions) + 1
        session = self.sessions[node]
        negotiated = 1 if version < 3 else 3
        send(f"WELCOME {negotiated} S{session}".encode())

        # The legacy count includes both the handshake and the BYE command.
        commands = 1
        while True:
            raw = rfile.readline(511)
            if not raw:
                return
            line = raw.split(b"\0", 1)[0].rstrip(b"\r\n")
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
            key_limit = 16
            if cmd == b"PUT" and len(parts) >= 3 and _alnum(parts[1], 1, key_limit) and 1 <= len(parts[2]) <= 64:
                key = parts[1]
                value = parts[2][:48]
                if key not in self.store:
                    if self.slots >= MAX_KEYS:
                        send(b"ERR FULL")
                        continue
                    self.store[key] = value
                    self.slots += 1
                    send(b"OK")
                else:
                    old_value = self.store[key]
                    if old_value == value:
                        send(b"OK")
                    else:
                        self.store[key] = value
                        send(b"OK " + old_value)
            elif cmd == b"GET" and len(parts) >= 2 and _alnum(parts[1], 1, key_limit):
                value = self.store.get(parts[1])
                if value is not None:
                    send(b"VAL " + value)
                else:
                    send(b"NIL" if negotiated == 1 else b"ERR NOTFOUND")
            elif cmd == b"DEL" and len(parts) >= 2 and _alnum(parts[1], 1, key_limit):
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


def _parse_handshake(raw: bytes) -> tuple[int, bytes] | None:
    raw = raw.rstrip(b"\r\n")
    parts = raw.split()
    if len(parts) < 2 or parts[0] != b"HELLO":
        return None
    match = _VERSION.match(parts[1])
    if match is None:
        return None
    suffix = parts[1][match.end():]
    if suffix:
        node = suffix
    elif len(parts) >= 3:
        node = parts[2]
    else:
        return None
    if not _alnum(node, 1, 8):
        return None
    version = int(match[0])
    if not 1 <= version <= 9:
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
