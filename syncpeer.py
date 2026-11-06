"""SyncPeer replication peer, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). A TCP
server on 127.0.0.1 (ephemeral port by default, printed as
``LISTENING <port>``), serving one client at a time; the key-value store
lives for the whole process. Protocol reference: ``docs/SPEC.md`` (mind
the drift warning; the engine's behavior is the contract).

Where the legacy peer differs from the spec, this follows the peer:

- a client asking for version 2 negotiates version 1; version 1 sessions
  answer a GET miss with ``NIL``;
- the version field is parsed like C ``strtol`` truncated to ``int``;
- session ids are per node name (``S<n>`` in order of first appearance);
- surplus tokens on any line are ignored;
- values are stored truncated to 48 bytes; overwriting a key with a
  different value answers ``OK <previous value>``;
- ``KEYS`` matches the prefix case-insensitively (ASCII) and lists keys
  newest-first by insertion (overwrites keep their position);
- the ``GOODBYE`` count includes the handshake and the ``BYE`` itself;
- an empty line stalls the connection's replies until the client leaves.
"""

from __future__ import annotations

import argparse
import re
import socket
import sys

MAX_KEYS = 4096
MAX_VALUE = 64
STORED_VALUE = 48

_NUMBER = re.compile(rb"([+-]?)(\d+)(.*)", re.S)


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered
        self.sessions: dict[bytes, int] = {}

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        raw = rfile.readline()
        if not raw:
            return
        handshake = self._handshake(raw.split())
        if handshake is None:
            send(b"ERR HANDSHAKE")
            return
        negotiated, node = handshake
        session = self.sessions.setdefault(node, len(self.sessions) + 1)
        send(b"WELCOME %d S%d" % (negotiated, session))

        commands = 1
        silent = False
        for raw in iter(rfile.readline, b""):
            line = raw.rstrip(b"\r\n")
            if not line:
                silent = True
            reply = self._command(line.split(), negotiated, commands + 1)
            commands += 1
            if reply is None:
                continue
            if not silent:
                for out in reply:
                    send(out)
            if reply and reply[-1].startswith(b"GOODBYE"):
                if silent:
                    # The legacy peer never closes a stalled connection.
                    for _ in iter(rfile.readline, b""):
                        pass
                return

    def _handshake(self, parts):
        if len(parts) < 2 or parts[0] != b"HELLO":
            return None
        match = _NUMBER.fullmatch(parts[1])
        if match is None:
            return None
        version = _c_int(match.group(1), match.group(2))
        if match.group(3):
            node = match.group(3)
        elif len(parts) >= 3:
            node = parts[2]
        else:
            return None
        if not 1 <= version <= 9 or not _alnum(node, 1, 8):
            return None
        negotiated = 1 if version == 2 else min(version, 3)
        return negotiated, node

    def _command(self, parts, negotiated, count):
        if not parts:
            return [b"ERR FMT"]
        cmd = parts[0]
        if cmd == b"BYE":
            return [b"GOODBYE %d" % count]
        if cmd == b"PUT" and len(parts) >= 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= MAX_VALUE:
            key, value = parts[1], parts[2][:STORED_VALUE]
            old = self.store.get(key)
            if old is None and len(self.store) >= MAX_KEYS:
                return [b"ERR FULL"]
            self.store[key] = value
            return [b"OK" if old is None or old == value else b"OK " + old]
        if cmd == b"GET" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
            value = self.store.get(parts[1])
            if value is not None:
                return [b"VAL " + value]
            return [b"NIL" if negotiated == 1 else b"ERR NOTFOUND"]
        if cmd == b"DEL" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
            if parts[1] in self.store:
                del self.store[parts[1]]
                return [b"OK"]
            return [b"ERR NOTFOUND"]
        if cmd == b"KEYS" and len(parts) >= 2 and len(parts[1]) <= 16:
            prefix = parts[1].lower()
            matches = [k for k in reversed(self.store) if k.lower().startswith(prefix)]
            return [b"KEY " + k for k in matches] + [b"END %d" % len(matches)]
        return [b"ERR FMT"]

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


def _c_int(sign: bytes, digits: bytes) -> int:
    """strtol (clamped to 64 bits) narrowed to a 32-bit C int."""
    value = int(digits) * (-1 if sign == b"-" else 1)
    value = max(-(1 << 63), min(value, (1 << 63) - 1))
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value >= 1 << 31 else value


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
