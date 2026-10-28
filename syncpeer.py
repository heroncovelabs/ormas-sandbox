"""SyncPeer replication peer, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). A TCP
server on 127.0.0.1 (ephemeral port by default, printed as
``LISTENING <port>``), serving one client at a time; the key-value store
lives for the whole process. Protocol reference: ``docs/SPEC.md`` (mind
the drift warning; the peer's behavior is the contract).
"""

from __future__ import annotations

import argparse
import socket
import sys

MAX_KEYS = 4096    # accepted writes, over the life of the process
MAX_VALUE = 48     # stored value length; longer values are truncated
MAX_TOKEN = 64     # longest PUT value token accepted at all
# Protocol version served for each requested version: 2 is answered as 1,
# everything above 3 is capped at 3.
NEGOTIATED = {1: 1, 2: 1, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 3}


class Peer:
    def __init__(self):
        self.store: dict[str, str] = {}  # insertion-ordered
        self.writes = 0  # every accepted write, never decremented
        self.entries: set[str] = set()  # live spellings in the index
        self.order: list[str] = []  # those spellings, oldest first
        self.sessions: dict[str, int] = {}
        self.version = 3

    # -- key index ----------------------------------------------------------

    def put(self, key: str, value: str) -> str | None:
        """Store ``key``; return the value it overwrote, if any."""
        # Capacity counts writes ever accepted: deleting frees no slot.
        if key not in self.store and self.writes >= MAX_KEYS:
            return _FULL
        previous = self.store.get(key)
        self.store[key] = value
        self.writes += 1
        if key not in self.entries:
            self.entries.add(key)
            self.order.append(key)
        return previous

    def delete(self, key: str) -> bool:
        if key not in self.store:
            return False
        del self.store[key]
        if key in self.entries:
            self.entries.discard(key)
            self.order.remove(key)
        return True

    def list_keys(self, prefix: str) -> list[str]:
        """Spellings under ``prefix``, most recently written first.

        Matching ignores case; every distinct spelling is listed.
        """
        folded = prefix.lower()
        return [key for key in reversed(self.order) if key.lower().startswith(folded)]

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: str) -> None:
            wfile.write((line + "\n").encode())
            wfile.flush()

        if not self.handshake(rfile, send):
            return

        commands = 1  # the handshake counts as the first command
        for raw in iter(rfile.readline, b""):
            line = raw.rstrip(b"\r\n").decode(errors="replace")
            if not line:
                continue  # empty lines are ignored and not counted
            commands += 1
            parts = line.split()
            cmd = parts[0] if parts else ""
            if cmd == "BYE":
                send(f"GOODBYE {commands}")
                return
            if cmd == "PUT":
                if len(parts) < 3 or not _alnum(parts[1], 1, 16) or len(parts[2]) > MAX_TOKEN:
                    send("ERR FMT")
                    continue
                key = parts[1]
                value = parts[2][:MAX_VALUE]
                previous = self.put(key, value)
                if previous is _FULL:
                    send("ERR FULL")
                elif previous is None or previous == value:
                    send("OK")
                else:
                    send(f"OK {previous}")
            elif cmd == "GET":
                key = parts[1] if len(parts) > 1 else ""
                if not _alnum(key, 1, 16):
                    send("ERR FMT")
                    continue
                value = self.store.get(key)
                if value is not None:
                    send(f"VAL {value}")
                else:
                    send("ERR NOTFOUND" if self.version >= 3 else "NIL")
            elif cmd == "DEL":
                key = parts[1] if len(parts) > 1 else ""
                if not _alnum(key, 1, 16):
                    send("ERR FMT")
                    continue
                send("OK" if self.delete(key) else "ERR NOTFOUND")
            elif cmd == "KEYS":
                # Any non-empty prefix fits, measured in bytes like a key.
                if len(parts) < 2 or len(parts[1].encode()) > 16:
                    send("ERR FMT")
                    continue
                prefix = parts[1]
                matches = self.list_keys(prefix)
                for key in matches:
                    send(f"KEY {key}")
                send(f"END {len(matches)}")
            else:
                send("ERR FMT")

    def handshake(self, rfile, send) -> bool:
        raw = rfile.readline()
        if not raw:
            return False
        parts = raw.rstrip(b"\r\n").decode(errors="replace").split()
        version = 0
        if len(parts) >= 3 and parts[0] == "HELLO" and _digits(parts[1]):
            version = int(parts[1])
        if not 1 <= version <= 9 or not _alnum(parts[2], 1, 8):
            send("ERR HANDSHAKE")
            return False
        self.version = NEGOTIATED[version]
        node = parts[2]
        if node not in self.sessions:
            self.sessions[node] = len(self.sessions) + 1
        send(f"WELCOME {self.version} S{self.sessions[node]}")
        return True

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


_FULL = object()  # sentinel: the store is full


def _digits(value: str) -> bool:
    """Digits, optionally with a single leading ``+``."""
    digits = value[1:] if value.startswith("+") else value
    return digits.isdigit() and digits.isascii()


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
