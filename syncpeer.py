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
STORED_VALUE_BYTES = 48


def _read_record(rfile) -> str | None:
    # The daemon uses a 512-byte fgets buffer and C-string line endings.
    raw = rfile.readline(511)
    if not raw:
        return None
    raw = re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]
    # Latin-1 keeps each wire byte intact, including arbitrary value bytes.
    return raw.decode("latin-1")


def _tokens(line: str) -> list[str]:
    return re.findall(r"\S+", line, flags=re.ASCII)


def _wire_alnum(value: str, lo: int, hi: int) -> bool:
    return value.isascii() and _alnum(value, lo, hi)


def _handshake(line: str) -> tuple[int, str] | None:
    # The numeric field is scanned as a C int; the node can immediately
    # follow its digits. Extra fields are ignored, as with command arguments.
    match = re.match(r"\s*(\S+)\s+([+-]?[0-9]+)", line, flags=re.ASCII)
    if match is None or match[1] != "HELLO":
        return None
    nodes = _tokens(line[match.end():])
    if not nodes or not _wire_alnum(nodes[0], 1, 8):
        return None
    # scanf converts through a signed long before narrowing to a signed int.
    number = max(-(1 << 63), min(int(match[2]), (1 << 63) - 1))
    version = (number + (1 << 31)) % (1 << 32) - (1 << 31)
    if not 1 <= version <= 9:
        return None
    return version, nodes[0]


class Peer:
    def __init__(self):
        self.store: dict[str, str] = {}  # insertion-ordered active records
        # Deletion leaves a tombstone in the daemon's fixed-size record array.
        self.slots_used = 0
        self.sessions: dict[str, int] = {}
        self.sessions_issued = 0

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: str) -> None:
            wfile.write((line + "\n").encode("latin-1"))
            wfile.flush()

        line = _read_record(rfile)
        if line is None:
            return
        hello = _handshake(line)
        if hello is None:
            send("ERR HANDSHAKE")
            return
        version, node = hello
        negotiated = 3 if version >= 3 else 1
        session = self.sessions.get(node)
        if session is None:
            self.sessions_issued += 1
            session = self.sessions_issued
            # Once the registry fills, new nodes get an unremembered token.
            if len(self.sessions) < MAX_SESSIONS:
                self.sessions[node] = session
        send(f"WELCOME {negotiated} S{session}")

        commands = 1  # The handshake and BYE both count as served records.
        for line in iter(lambda: _read_record(rfile), None):
            if not line:
                continue
            commands += 1
            parts = _tokens(line)
            if not parts:
                send("ERR FMT")
                continue
            cmd = parts[0]
            if cmd == "BYE":
                send(f"GOODBYE {commands}")
                return
            if (
                cmd == "PUT"
                and len(parts) >= 3
                and _wire_alnum(parts[1], 1, 16)
                and 1 <= len(parts[2]) <= 64
            ):
                key, value = parts[1], parts[2][:STORED_VALUE_BYTES]
                previous = self.store.get(key)
                if previous is None:
                    if self.slots_used >= MAX_KEYS:
                        send("ERR FULL")
                        continue
                    self.slots_used += 1
                self.store[key] = value
                send(f"OK {previous}" if previous is not None and previous != value else "OK")
            elif cmd == "GET" and len(parts) >= 2 and _wire_alnum(parts[1], 1, 16):
                value = self.store.get(parts[1])
                missing = "NIL" if negotiated == 1 else "ERR NOTFOUND"
                send(f"VAL {value}" if value is not None else missing)
            elif cmd == "DEL" and len(parts) >= 2 and _wire_alnum(parts[1], 1, 16):
                if parts[1] in self.store:
                    del self.store[parts[1]]
                    send("OK")
                else:
                    send("ERR NOTFOUND")
            elif cmd == "KEYS" and len(parts) >= 2 and len(parts[1]) <= 16:
                prefix = parts[1].lower()
                matches = [k for k in reversed(self.store) if k.lower().startswith(prefix)]
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
