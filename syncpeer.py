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
MAX_VALUE_CHARS = 48
_VERSION_PREFIX = re.compile(r"[+-]?[0-9]+")


class Peer:
    def __init__(self):
        self.store: dict[str, str] = {}  # insertion-ordered
        self.sessions: dict[str, int] = {}

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: str) -> None:
            wfile.write((line + "\n").encode())
            wfile.flush()

        raw = rfile.readline()
        if not raw:
            return
        parts = raw.decode(errors="replace").strip().split()
        version_match = _VERSION_PREFIX.match(parts[1]) if len(parts) >= 2 else None
        if (
            len(parts) < 3
            or parts[0] != "HELLO"
            or version_match is None
            or not 1 <= int(version_match.group()) <= 9
            or not _alnum(parts[2], 1, 8)
        ):
            send("ERR HANDSHAKE")
            return
        version = int(version_match.group())
        negotiated = 1 if version <= 2 else 3
        node = parts[2]
        if node not in self.sessions:
            self.sessions[node] = len(self.sessions) + 1
        send(f"WELCOME {negotiated} S{self.sessions[node]}")

        commands = 1
        for raw in iter(rfile.readline, b""):
            line = raw.decode(errors="replace").rstrip("\r\n")
            if not line:
                continue
            commands += 1
            parts = line.split()
            cmd = parts[0]
            if cmd == "BYE":
                send(f"GOODBYE {commands}")
                return
            if cmd == "PUT" and len(parts) >= 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= 64:
                key = parts[1]
                value = parts[2][:MAX_VALUE_CHARS]
                previous = self.store.get(key)
                if previous is None and len(self.store) >= MAX_KEYS:
                    send("ERR FULL")
                    continue
                self.store[key] = value
                send(f"OK {previous}" if previous is not None and previous != value else "OK")
            elif cmd == "GET" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                value = self.store.get(parts[1])
                if value is None:
                    send("NIL" if negotiated == 1 else "ERR NOTFOUND")
                else:
                    send(f"VAL {value}")
            elif cmd == "DEL" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                if parts[1] in self.store:
                    del self.store[parts[1]]
                    send("OK")
                else:
                    send("ERR NOTFOUND")
            elif cmd == "KEYS" and len(parts) >= 2 and len(parts[1]) <= 16:
                prefix = parts[1].lower()
                matches = [
                    k for k in reversed(self.store) if k.lower().startswith(prefix)
                ]
                matches.sort(key=str.lower, reverse=True)
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


def _alnum(value: str, lo: int, hi: int) -> bool:
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
