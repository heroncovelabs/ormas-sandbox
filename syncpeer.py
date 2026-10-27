"""SyncPeer replication peer, Python implementation.

Drop-in wire-level replacement for the retired legacy daemon (see
``legacy/README.md``). A TCP server on 127.0.0.1 (ephemeral port by
default, printed as ``LISTENING <port>``), serving one client at a time;
the key-value store and session registry live for the whole process.

Protocol reference: ``docs/SPEC.md``. The spec has drifted; wherever it
disagrees with the retired daemon, the daemon's wire behavior is the
contract, and this module reproduces it.
"""

from __future__ import annotations

import argparse
import socket
import sys

MAX_KEYS = 4096
MAX_VALUE_IN = 64   # accepted value length (bytes)
MAX_VALUE_OUT = 48  # stored/echoed value length (bytes)
MAX_KEY = 16
MAX_NODE = 8

_WS = b" \t\r\n\v\f"


class Peer:
    def __init__(self):
        self.store: dict[bytes, bytes] = {}  # insertion-ordered
        self.sessions: dict[bytes, int] = {}  # node -> session number
        self.inserted = 0  # distinct keys ever inserted (never decremented)

    # -- one connection -----------------------------------------------------

    def serve_connection(self, rfile, wfile) -> None:
        def send(line: bytes) -> None:
            wfile.write(line + b"\n")
            wfile.flush()

        raw = rfile.readline()
        if not raw:
            return
        line = raw.rstrip(b"\r\n")
        hello = _parse_hello(line)
        if hello is None:
            send(b"ERR HANDSHAKE")
            return
        version, node = hello
        session = self.sessions.get(node)
        if session is None:
            session = len(self.sessions) + 1
            self.sessions[node] = session
        negotiated = 1 if version < 3 else 3
        send(b"WELCOME %d S%d" % (negotiated, session))

        count = 1  # the handshake itself
        for raw in iter(rfile.readline, b""):
            line = raw.rstrip(b"\r\n")
            if not line:
                continue
            count += 1
            parts = line.split()
            if not parts:
                send(b"ERR FMT")
                continue
            cmd = parts[0]
            if cmd == b"BYE":
                send(b"GOODBYE %d" % count)
                return
            if cmd == b"PUT":
                if (
                    len(parts) >= 3
                    and _alnum(parts[1], 1, MAX_KEY)
                    and 1 <= len(parts[2]) <= MAX_VALUE_IN
                ):
                    key = parts[1]
                    value = parts[2][:MAX_VALUE_OUT]
                    old = self.store.get(key)
                    if old is not None:
                        self.store[key] = value
                        if old == value:
                            send(b"OK")
                        else:
                            send(b"OK " + old)
                    elif self.inserted >= MAX_KEYS:
                        send(b"ERR FULL")
                    else:
                        self.store[key] = value
                        self.inserted += 1
                        send(b"OK")
                else:
                    send(b"ERR FMT")
            elif cmd == b"GET":
                if len(parts) >= 2 and _alnum(parts[1], 1, MAX_KEY):
                    value = self.store.get(parts[1])
                    if value is not None:
                        send(b"VAL " + value)
                    elif negotiated == 1:
                        send(b"NIL")
                    else:
                        send(b"ERR NOTFOUND")
                else:
                    send(b"ERR FMT")
            elif cmd == b"DEL":
                if len(parts) >= 2 and _alnum(parts[1], 1, MAX_KEY):
                    if parts[1] in self.store:
                        del self.store[parts[1]]
                        send(b"OK")
                    else:
                        send(b"ERR NOTFOUND")
                else:
                    send(b"ERR FMT")
            elif cmd == b"KEYS":
                if len(parts) >= 2 and 1 <= len(parts[1]) <= MAX_KEY:
                    prefix = parts[1].lower()
                    matches = [
                        key
                        for key in reversed(self.store)
                        if key.lower().startswith(prefix)
                    ]
                    for key in matches:
                        send(b"KEY " + key)
                    send(b"END %d" % len(matches))
                else:
                    send(b"ERR FMT")
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


def _parse_hello(line: bytes):
    """Reproduce the daemon's handshake parsing: literal ``HELLO`` token,
    then ``%d %s`` over the remainder of the line."""
    n = len(line)
    i = 0
    while i < n and line[i:i + 1] in _WS:
        i += 1
    start = i
    while i < n and line[i:i + 1] not in _WS:
        i += 1
    if line[start:i] != b"HELLO":
        return None
    rest = line[i:]
    m = len(rest)
    j = 0
    while j < m and rest[j:j + 1] in _WS:
        j += 1
    k = j
    if k < m and rest[k:k + 1] in b"+-":
        k += 1
    d = k
    while d < m and rest[d:d + 1].isdigit():
        d += 1
    if d == k:
        return None
    try:
        version = int(rest[j:d])
    except ValueError:
        return None
    while d < m and rest[d:d + 1] in _WS:
        d += 1
    s = d
    while d < m and rest[d:d + 1] not in _WS:
        d += 1
    node = rest[s:d]
    if not 1 <= version <= 9 or not _alnum(node, 1, MAX_NODE):
        return None
    return version, node


def _alnum(value: bytes, lo: int, hi: int) -> bool:
    return lo <= len(value) <= hi and value.isalnum() and value.isascii()


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
