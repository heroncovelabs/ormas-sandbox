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
MAX_RECORD = 511  # fgets' 512-byte buffer includes a terminating NUL.
MAX_VALUE = 48


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered
        self.insertions = 0  # Deleted entries still occupy legacy store slots.
        self.sessions: dict[bytes, int] = {}
        self.session_count = 0

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        line = _read_record(rfile)
        if line is None:
            return
        handshake = _handshake(line)
        if handshake is None:
            send(b"ERR HANDSHAKE")
            return
        version, node = handshake
        negotiated = 1 if version <= 2 else 3
        session = self.sessions.get(node)
        if session is None:
            self.session_count += 1
            session = self.session_count
            # Once the registry fills, new identities receive uncached tokens.
            if len(self.sessions) < MAX_SESSIONS:
                self.sessions[node] = session
        send(f"WELCOME {negotiated} S{session}".encode())

        commands = 1  # Count the handshake and every nonempty record, including BYE.
        while (line := _read_record(rfile)) is not None:
            if not line:
                continue
            commands += 1
            # sscanf consumes only these fields, with fixed byte widths.
            cmd, rest = _field(line, 15)
            key, rest = _field(rest, 127)
            value, _ = _field(rest, 127)
            if cmd == b"BYE":
                send(f"GOODBYE {commands}".encode())
                return
            if cmd == b"PUT" and _alnum(key, 1, 16) and 1 <= len(value) <= 64:
                previous = self.store.get(key)
                if previous is None:
                    if self.insertions >= MAX_KEYS:
                        send(b"ERR FULL")
                        continue
                    self.insertions += 1
                value = value[:MAX_VALUE]
                self.store[key] = value
                if previous is not None and previous != value:
                    send(b"OK " + previous)
                else:
                    send(b"OK")
            elif cmd == b"GET" and _alnum(key, 1, 16):
                value = self.store.get(key)
                if value is not None:
                    send(b"VAL " + value)
                else:
                    send(b"NIL" if negotiated == 1 else b"ERR NOTFOUND")
            elif cmd == b"DEL" and _alnum(key, 1, 16):
                if key in self.store:
                    del self.store[key]
                    send(b"OK")
                else:
                    send(b"ERR NOTFOUND")
            elif cmd == b"KEYS" and key and len(key) <= 16:
                # ASCII-insensitive prefixes, newest insertion first;
                # overwrites retain their position and reinserts move to the front.
                prefix = key.lower()
                matches = [
                    stored_key for stored_key in reversed(self.store)
                    if stored_key.lower().startswith(prefix)
                ]
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


def _read_record(rfile) -> bytes | None:
    raw = rfile.readline(MAX_RECORD)
    if not raw:
        return None
    # C strings end at NUL, and the daemon cuts at the first CR or LF.
    return re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]


def _field(raw: bytes, width: int) -> tuple[bytes, bytes]:
    """Consume a width-limited scanf %s field using C-locale whitespace."""
    raw = raw.lstrip()
    parts = raw.split(None, 1)
    if not parts:
        return b"", b""
    field = parts[0][:width]
    return field, raw[len(field):]


def _handshake(line: bytes) -> tuple[int, bytes] | None:
    cmd, rest = _field(line, 15)
    rest = rest.lstrip()
    number = re.match(rb"[+-]?[0-9]+", rest)
    if cmd != b"HELLO" or number is None:
        return None
    # scanf's %d accepts a signed decimal prefix, then narrows strtol's result.
    version = max(-(1 << 63), min((1 << 63) - 1, int(number.group())))
    version = (version + (1 << 31)) % (1 << 32) - (1 << 31)
    node, _ = _field(rest[number.end():], 63)
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
