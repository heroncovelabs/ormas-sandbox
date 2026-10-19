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
_MAX_SESSIONS = 1024
_LINE_BYTES = 511
_STORED_VALUE_BYTES = 48


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered live keys
        # Deleted entries continue to occupy slots in the daemon's fixed table.
        self._key_slots = 0
        self.connections = 0
        self._sessions: dict[bytes, str] = {}
        self._session_count = 0

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: str | bytes) -> None:
            if isinstance(line, str):
                line = line.encode("ascii")
            wfile.write(line + b"\n")
            wfile.flush()

        self.connections += 1
        # The daemon's 512-byte handshake buffer holds at most 511 input
        # bytes. Any remainder stays in the stream for command processing.
        raw = rfile.readline(_LINE_BYTES)
        if not raw:
            return
        # The daemon scans an ASCII command, a decimal integer, then a client
        # token. Integer scanning can stop directly before the client token;
        # trailing fields are ignored; NUL, CR, and LF terminate the string.
        handshake = re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]
        version_match = re.match(rb"\s*HELLO\s+([+-]?[0-9]+)", handshake)
        if version_match is None:
            send("ERR HANDSHAKE")
            return
        clients = handshake[version_match.end():].split()
        if not clients or not 1 <= len(clients[0]) <= 8 or not clients[0].isalnum():
            send("ERR HANDSHAKE")
            return

        # Match the daemon's signed long conversion followed by a 32-bit int
        # assignment, including overflow, without Python's integer-string limit.
        token = version_match[1]
        digits = token.lstrip(b"+-").lstrip(b"0") or b"0"
        magnitude = int(digits) if len(digits) <= 19 else 1 << 63
        version = -magnitude if token.startswith(b"-") else magnitude
        version = max(-(1 << 63), min(version, (1 << 63) - 1))
        version = (version + (1 << 31)) % (1 << 32) - (1 << 31)
        if not 1 <= version <= 9:
            send("ERR HANDSHAKE")
            return
        negotiated = 3 if version >= 3 else 1
        client = clients[0]
        session = self._sessions.get(client)
        if session is None:
            self._session_count += 1
            session = f"S{self._session_count}"
            # Only the first 1024 distinct clients retain reconnect identities.
            if len(self._sessions) < _MAX_SESSIONS:
                self._sessions[client] = session
        send(f"WELCOME {negotiated} {session}")

        # The handshake and BYE both contribute to the connection's count.
        commands = 1
        for raw in iter(lambda: rfile.readline(_LINE_BYTES), b""):
            line = re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]
            if not line:
                continue
            commands += 1
            # Byte splitting matches C's ASCII whitespace and preserves values,
            # including invalid UTF-8 and truncation within multibyte characters.
            parts = line.split()
            cmd = parts[0] if parts else b""
            if cmd == b"BYE":
                send(f"GOODBYE {commands}")
                return
            if cmd == b"PUT" and len(parts) >= 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= 64:
                key, value = parts[1:3]
                previous = self.store.get(key)
                if previous is None:
                    if self._key_slots >= MAX_KEYS:
                        send("ERR FULL")
                        continue
                    self._key_slots += 1
                value = value[:_STORED_VALUE_BYTES]
                self.store[key] = value
                send(b"OK " + previous if previous is not None and previous != value else b"OK")
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
                prefix = parts[1].lower()
                matches = [k for k in reversed(self.store) if k.lower().startswith(prefix)]
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
