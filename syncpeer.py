"""SyncPeer replication peer, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). A TCP
server on 127.0.0.1 (ephemeral port by default, printed as
``LISTENING <port>``), serving one client at a time; the key-value store
and session registry live for the whole process. Protocol reference:
``docs/SPEC.md``, but the engine's observed wire behavior is the contract
wherever the spec drifted (see the notes on each method below).
"""

from __future__ import annotations

import argparse
import re
import socket
import sys

MAX_KEYS = 4096
MAX_VALUE = 64  # longest value accepted by PUT
STORED_VALUE = 48  # values are stored truncated to this many characters

_VERSION = re.compile(r"\+?[0-9]+")
_ASCII_LOWER = {ord(c): ord(c) + 32 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}


class Peer:
    def __init__(self):
        self.store: dict[str, str] = {}  # insertion-ordered
        self.sessions: dict[str, int] = {}  # node name -> session number

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: str) -> None:
            wfile.write((line + "\n").encode())
            wfile.flush()

        raw = rfile.readline()
        if not raw:
            return
        # Handshake extras are ignored; session ids are per node name and are
        # only allocated for successful handshakes.
        parts = raw.decode(errors="replace").strip().split()
        version = _parse_version(parts[1]) if len(parts) >= 3 else None
        if (
            version is None
            or len(parts) < 3
            or parts[0] != "HELLO"
            or not _ascii_alnum(parts[2], 1, 8)
        ):
            send("ERR HANDSHAKE")
            return
        # The daemon negotiates versions 1 and 2 down to 1, and 3+ to 3.
        negotiated = 1 if version <= 2 else 3
        session = self.sessions.setdefault(parts[2], len(self.sessions) + 1)
        send(f"WELCOME {negotiated} S{session}")

        commands = 1  # the HELLO line counts toward GOODBYE
        for raw in iter(rfile.readline, b""):
            line = raw.decode(errors="replace").rstrip("\r\n")
            if not line:  # empty lines are ignored and not counted
                continue
            commands += 1
            parts = line.split()
            cmd = parts[0] if parts else ""
            if cmd == "BYE":
                send(f"GOODBYE {commands}")
                return
            if cmd == "PUT" and len(parts) >= 3 and _ascii_alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= MAX_VALUE:
                if parts[1] not in self.store and len(self.store) >= MAX_KEYS:
                    send("ERR FULL")
                    continue
                value = parts[2][:STORED_VALUE]
                old = self.store.get(parts[1])
                self.store[parts[1]] = value  # overwrite keeps the key's position
                # Overwrites echo the previous stored value when it changed.
                send(f"OK {old}" if old is not None and old != value else "OK")
            elif cmd == "GET" and len(parts) >= 2 and _ascii_alnum(parts[1], 1, 16):
                value = self.store.get(parts[1])
                if value is not None:
                    send(f"VAL {value}")
                else:
                    # Version 1 sessions report a missing key as NIL.
                    send("NIL" if negotiated == 1 else "ERR NOTFOUND")
            elif cmd == "DEL" and len(parts) >= 2 and _ascii_alnum(parts[1], 1, 16):
                if parts[1] in self.store:
                    del self.store[parts[1]]
                    send("OK")
                else:
                    send("ERR NOTFOUND")
            elif cmd == "KEYS" and len(parts) >= 2 and len(parts[1]) <= 16:
                # Prefix matching is ASCII case-insensitive; the daemon lists
                # matches in reverse insertion order.
                prefix = parts[1].translate(_ASCII_LOWER)
                matches = [k for k in reversed(self.store) if k.translate(_ASCII_LOWER).startswith(prefix)]
                for key in matches:
                    send(f"KEY {key}")
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


def _parse_version(text: str) -> int | None:
    if not _VERSION.fullmatch(text):
        return None
    value = int(text)
    return value if 1 <= value <= 9 else None


def _ascii_alnum(value: str, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and value.isascii() and value.isalnum()


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
