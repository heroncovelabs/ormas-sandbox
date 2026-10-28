"""LockCore lease manager, Python implementation.

Replaces the retired legacy binary (see ``legacy/README.md``). One
session per process: commands on stdin, result lines on stdout, trailer
at end of input. Format reference: ``docs/SPEC.md`` (mind the drift
warning; the engine's behavior is the contract).
"""

from __future__ import annotations

import sys


class Resource:
    __slots__ = ("name", "holder", "expiry", "orig", "queue", "renews", "last_expired", "sweeps_since_expiry")

    def __init__(self, name: str):
        self.name = name
        self.holder: str | None = None
        self.expiry = 0
        self.orig = 0
        self.queue: list[tuple[str, int]] = []  # (client, ttl)
        self.renews = 0  # Track number of renewals for expiry calculation
        self.last_expired: str | None = None  # Client whose lease last expired on this resource
        self.sweeps_since_expiry = 0  # Sweeps since the last expiry


class Engine:
    def __init__(self, out=None):
        self.resources: list[Resource] = []
        self.by_name: dict[str, Resource] = {}
        self.client_display: dict[str, str] = {}  # normalized -> original case
        self.now = 0
        self.c_acq = 0
        self.c_ren = 0
        self.c_swp = 0
        self.c_rej = 0
        self.out = out if out is not None else sys.stdout

    def _emit(self, line: str) -> None:
        self.out.write(line + "\n")

    def _reject(self, echo: str, code: str) -> None:
        self._emit(f"N {echo} {code}")
        self.c_rej += 1

    def _holds_of(self, client: str) -> int:
        return sum(1 for r in self.resources if r.holder == client)

    def _grant(self, r: Resource, client: str, ttl: int, client_original: str = None) -> None:
        r.holder = client
        r.orig = ttl
        r.expiry = self.now + ttl
        r.renews = 0  # Reset renewal count on new grant
        # Clear grace reclaim status only if the granted client is the one who expired
        if r.last_expired == client:
            r.last_expired = None
            r.sweeps_since_expiry = 0
        # Store original case for display (only on first acquire)
        if client_original is not None and client not in self.client_display:
            self.client_display[client] = client_original
        display_client = self.client_display.get(client, client)
        self._emit(f"G {r.name} {display_client}")

    def _drain_free(self) -> int:
        granted = 0
        for r in self.resources:  # creation order
            if r.holder is None and r.queue:
                client, ttl = r.queue.pop(0)
                self._grant(r, client, ttl, None)  # No original case, use stored display
                granted += 1
        return granted

    def _normalize(self, s: str) -> str:
        """Normalize client/resource ID to lowercase for case-insensitive matching."""
        return s.lower()

    def _effective_ttl(self, rid: str, ttl: int) -> int:
        """Apply long-name cap: if resource name >= 6 chars, cap TTL at 100."""
        if len(rid) >= 6:
            return min(ttl, 100)
        return ttl

    def handle(self, line: str) -> None:
        parts = line.rstrip("\r\n").split()
        if not parts:
            return
        kind = parts[0]
        cid = parts[1] if len(parts) > 1 else ""
        cli_ok = 1 <= len(cid) <= 8 and cid.isalnum()
        echo = cid if cli_ok else "????????"
        rid = parts[2] if len(parts) > 2 else ""

        if kind == "A":
            # Accept trailing tokens - only validate first 4 parts
            if len(parts) < 4:
                self._reject(echo, "FMT")
                return
            if not cli_ok:
                self._reject("????????", "FMT")
                return
            if not (1 <= len(rid) <= 8 and rid.isalnum()):
                self._reject(echo, "FMT")
                return
            ttok = parts[3]
            if not (ttok.isdigit() and 1 <= len(ttok) <= 3):
                self._reject(cid, "TTL")
                return
            ttl = int(ttok)
            if not 1 <= ttl <= 999:
                self._reject(cid, "TTL")
                return
            
            # Apply long-name cap to TTL
            eff_ttl = self._effective_ttl(rid, ttl)
            
            # Normalize IDs for case-insensitive matching
            cid_norm = self._normalize(cid)
            rid_norm = self._normalize(rid)
            
            r = self.by_name.get(rid_norm)
            if r is not None and (
                r.holder == cid_norm or any(w == cid_norm for w, _ in r.queue)
            ):
                # Use stored display case for reject message
                display_cid = self.client_display.get(cid_norm, cid)
                self._reject(display_cid, "STATE")
                return
            if r is None:
                r = Resource(rid)  # Keep original case for display
                self.resources.append(r)
                self.by_name[rid_norm] = r
            # Store client display case on first encounter (for both grant and queue)
            if cid_norm not in self.client_display:
                self.client_display[cid_norm] = cid
            if r.holder is None:
                self._grant(r, cid_norm, eff_ttl, cid)
            else:
                # Check for grace reclaim priority: if this client was the last to expire
                # and it's within the grace window (< 10 sweeps), insert at front of queue
                if r.last_expired == cid_norm and r.sweeps_since_expiry < 10:
                    r.queue.insert(0, (cid_norm, eff_ttl))
                else:
                    r.queue.append((cid_norm, eff_ttl))
                self._emit(f"Q {len(r.queue)}")
            self.c_acq += 1
            self.now += 1
            return

        if kind == "R":
            # Accept trailing tokens - only validate first 3 parts
            if len(parts) < 3:
                self._reject(echo, "FMT")
                return
            if not cli_ok:
                self._reject("????????", "FMT")
                return
            if not (1 <= len(rid) <= 8 and rid.isalnum()):
                self._reject(echo, "FMT")
                return
            
            # Normalize IDs
            cid_norm = self._normalize(cid)
            rid_norm = self._normalize(rid)
            
            # Store client display case on first encounter
            if cid_norm not in self.client_display:
                self.client_display[cid_norm] = cid
            
            r = self.by_name.get(rid_norm)
            # Renew rejected if lease doesn't exist, holder mismatch, or already expired
            if r is None or r.holder != cid_norm or r.expiry <= self.now:
                display_cid = self.client_display.get(cid_norm, cid)
                self._reject(display_cid, "STATE")
                return
            # Renew adjusts expiry: expiry = now + orig - (renews + 1)
            # Each renewal effectively "uses up" one tick of the lease
            r.renews += 1
            r.expiry = self.now + r.orig - r.renews
            self._emit(f"OK {self._holds_of(cid_norm)}")
            self.c_ren += 1
            self.now += 1
            return

        if kind == "E":
            # Accept trailing tokens - just need at least the command
            if len(parts) < 1:
                self._reject(echo, "FMT")
                return
            released = 0
            for r in self.resources:
                if r.holder is not None and r.expiry <= self.now:
                    r.last_expired = r.holder  # Track who expired
                    r.sweeps_since_expiry = 0  # Reset sweep counter
                    r.holder = None
                    released += 1
                elif r.last_expired is not None:
                    r.sweeps_since_expiry += 1  # Increment for resources with recent expiry
            granted = self._drain_free()
            self._emit(f"EEND {released} {granted}")
            self.c_swp += 1
            self.now += 1
            return

        if kind == "L":
            # Accept trailing tokens - only validate first 2 parts
            if len(parts) < 2:
                self._reject(echo, "FMT")
                return
            if not cli_ok:
                self._reject("????????", "FMT")
                return
            
            # Normalize client ID and store display case
            cid_norm = self._normalize(cid)
            if cid_norm not in self.client_display:
                self.client_display[cid_norm] = cid
            
            # Idempotent: releasing a client with no leases succeeds with LEND 0
            released = 0
            for r in self.resources:
                if r.holder == cid_norm:
                    r.holder = None
                    # Clear grace reclaim status when holder releases
                    r.last_expired = None
                    r.sweeps_since_expiry = 0
                    released += 1
            self._drain_free()
            self._emit(f"LEND {released}")
            self.now += 1
            return

        self._reject(echo, "FMT")

    def finish(self) -> None:
        self._emit(f"X {self.c_acq} {self.c_ren} {self.c_swp} {self.c_rej}")


def main() -> None:
    engine = Engine()
    for line in sys.stdin:
        engine.handle(line)
    engine.finish()


if __name__ == "__main__":
    main()
