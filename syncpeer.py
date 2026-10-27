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

# Slots are never reclaimed: deleted keys leave a dead slot behind, so the
# capacity counts every key ever inserted (as the legacy peer does).
MAX_KEYS = 4096
# Stored values are cut to this many bytes (the peer accepts up to 64).
STORED_VALUE_LEN = 48

_WS = re.compile(rb"[ \t\n\r\x0b\x0c]+")
_ALNUM = re.compile(rb"[A-Za-z0-9]+")
# C-style "%d%s": optional sign, digits, then the node may follow directly.
_HELLO_VERSION = re.compile(rb"([+-]?[0-9]+)(.*)", re.S)


class Peer:
    def __init__(self):
        # Insertion-ordered slots: [key, value, alive]; newest listed first.
        self.slots: list[list] = []
        self.index: dict[bytes, list] = {}  # live key -> slot
        self.sessions: dict[bytes, int] = {}  # node -> session number

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        raw = rfile.readline()
        if not raw:
            return
        negotiated, node = _parse_hello(_tokens(raw))
        if negotiated is None:
            send(b"ERR HANDSHAKE")
            return
        session = self.sessions.setdefault(node, len(self.sessions) + 1)
        send(b"WELCOME %d S%d" % (negotiated, session))

        commands = 1  # the handshake counts
        for raw in iter(rfile.readline, b""):
            line = raw.rstrip(b"\r\n")
            if not line:
                continue
            commands += 1
            parts = _tokens(line)
            cmd = parts[0] if parts else b""
            if cmd == b"BYE":
                send(b"GOODBYE %d" % commands)
                return
            if cmd == b"PUT" and len(parts) >= 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= 64:
                key, value = parts[1], parts[2][:STORED_VALUE_LEN]
                slot = self.index.get(key)
                if slot is None:
                    if len(self.slots) >= MAX_KEYS:
                        send(b"ERR FULL")
                        continue
                    slot = [key, value, True]
                    self.slots.append(slot)
                    self.index[key] = slot
                    send(b"OK")
                elif slot[1] != value:
                    old, slot[1] = slot[1], value
                    send(b"OK " + old)
                else:
                    send(b"OK")
            elif cmd == b"GET" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                slot = self.index.get(parts[1])
                if slot is not None:
                    send(b"VAL " + slot[1])
                else:
                    send(b"NIL" if negotiated == 1 else b"ERR NOTFOUND")
            elif cmd == b"DEL" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                slot = self.index.pop(parts[1], None)
                if slot is not None:
                    slot[2] = False
                    send(b"OK")
                else:
                    send(b"ERR NOTFOUND")
            elif cmd == b"KEYS" and len(parts) >= 2 and len(parts[1]) <= 16:
                prefix = parts[1].lower()
                matches = [s[0] for s in reversed(self.slots) if s[2] and s[0].lower().startswith(prefix)]
                for key in matches:
                    send(b"KEY " + key)
                send(b"END %d" % len(matches))
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


def _tokens(line: bytes) -> list[bytes]:
    return [t for t in _WS.split(line) if t]


def _parse_hello(parts: list[bytes]):
    """Return (negotiated, node), or (None, None) for a bad handshake."""
    if len(parts) < 2 or parts[0] != b"HELLO":
        return None, None
    match = _HELLO_VERSION.fullmatch(parts[1])
    if match is None:
        return None, None
    # strtol (64-bit, saturating) stored into a 32-bit int.
    version = max(-(1 << 63), min(int(match.group(1)), (1 << 63) - 1))
    version &= 0xFFFFFFFF
    if version >= 1 << 31:
        version -= 1 << 32
    node = match.group(2) or (parts[2] if len(parts) > 2 else b"")
    if not 1 <= version <= 9 or not _alnum(node, 1, 8):
        return None, None
    return (1 if version < 3 else 3), node


def _alnum(value: bytes, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and _ALNUM.fullmatch(value) is not None


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
