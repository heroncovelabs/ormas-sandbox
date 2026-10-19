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


class Peer:
    def __init__(self):
        self.store: dict[str, str] = {}  # insertion-ordered
        self.allocated_keys = 0
        self.session_ids: dict[bytes, int] = {}
        self.next_session_id = 1

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: str) -> None:
            wfile.write((line + "\n").encode("latin-1"))
            wfile.flush()

        # The daemon uses a 512-byte fgets buffer, including its terminating
        # NUL. An overlong wire line is therefore processed in 511-byte chunks.
        raw = rfile.readline(511)
        if not raw:
            return
        # The legacy scanner consumes a decimal prefix, then a node token;
        # whitespace between the number and node is optional.
        parts = _line(raw).split(None, 1)
        number = re.match(rb"[+-]?[0-9]+", parts[1]) if len(parts) == 2 else None
        nodes = parts[1][number.end():].split() if number is not None else []
        requested = _version(number[0]) if number is not None else 0
        if (
            not parts
            or parts[0] != b"HELLO"
            or not 1 <= requested <= 9
            or not nodes
            or not _alnum(nodes[0].decode("latin-1"), 1, 8)
        ):
            send("ERR HANDSHAKE")
            return
        # Version 2 clients use the version 1 protocol on the legacy wire.
        negotiated = 1 if requested < 3 else 3
        session_id = self.session_ids.get(nodes[0])
        if session_id is None:
            session_id = self.next_session_id
            self.next_session_id += 1
            # The daemon remembers only the first 1024 distinct valid nodes.
            # Later nodes receive a fresh ID on every successful handshake.
            if len(self.session_ids) < 1024:
                self.session_ids[nodes[0]] = session_id
        send(f"WELCOME {negotiated} S{session_id}")

        # The handshake and BYE itself both count as served commands.
        commands = 1
        for raw in iter(lambda: rfile.readline(511), b""):
            line = _line(raw)
            if not line:
                continue
            commands += 1
            parts = [part.decode("latin-1") for part in line.split()]
            if not parts:
                send("ERR FMT")
                continue
            cmd = parts[0]
            if cmd == "BYE":
                send(f"GOODBYE {commands}")
                return
            if cmd == "PUT" and len(parts) >= 3 and _alnum(parts[1], 1, 16) and 1 <= len(parts[2]) <= 64:
                if parts[1] not in self.store:
                    # Deleted entries still occupy slots in the daemon's
                    # fixed table; only overwrites avoid allocating a slot.
                    if self.allocated_keys >= MAX_KEYS:
                        send("ERR FULL")
                        continue
                    self.allocated_keys += 1
                previous = self.store.get(parts[1])
                # Latin-1 keeps each wire byte as one character. The daemon
                # accepts up to 64 bytes but stores and compares only 48.
                value = parts[2][:48]
                self.store[parts[1]] = value
                send(f"OK {previous}" if previous is not None and previous != value else "OK")
            elif cmd == "GET" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                value = self.store.get(parts[1])
                send(f"VAL {value}" if value is not None else "NIL" if negotiated == 1 else "ERR NOTFOUND")
            elif cmd == "DEL" and len(parts) >= 2 and _alnum(parts[1], 1, 16):
                if parts[1] in self.store:
                    del self.store[parts[1]]
                    send("OK")
                else:
                    send("ERR NOTFOUND")
            elif cmd == "KEYS" and len(parts) >= 2 and len(parts[1]) <= 16:
                # The daemon walks newest keys first and folds ASCII case
                # when matching prefixes. Overwrites retain their position.
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


def _line(raw: bytes) -> bytes:
    # C strings end at NUL, and the daemon discards the first CR/LF onward.
    return re.split(rb"[\x00\r\n]", raw, maxsplit=1)[0]


def _version(token: bytes) -> int:
    # Match the legacy %d conversion: saturate a signed 64-bit intermediate,
    # then retain the low 32 bits. Avoid Python's limit on huge integer strings.
    negative = token.startswith(b"-")
    digits = token.lstrip(b"+-").lstrip(b"0") or b"0"
    limit = (1 << 63) if negative else (1 << 63) - 1
    magnitude = limit if len(digits) > 19 else min(int(digits), limit)
    return (-magnitude if negative else magnitude) & 0xFFFFFFFF


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
