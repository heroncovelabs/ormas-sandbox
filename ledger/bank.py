"""The command side of an event-sourced ledger.

Every state change is expressed as an event appended to a single ordered log and
applied through ``ledger.events.apply_event``. The live balances must therefore
always equal ``replay(history())``, and a bank rebuilt from a history must match
the original.
"""

from ledger.events import AccountOpened, Deposited, Withdrawn, apply_event, replay


class InsufficientFunds(Exception):
    """Raised when a withdrawal or transfer exceeds the available balance."""


class Bank:
    """A set of accounts whose balances are derived from an event log."""

    def __init__(self):
        self._log = []
        self._balances = {}

    # ----- internal helpers -------------------------------------------------

    def _require_account(self, account_id):
        if account_id not in self._balances:
            raise ValueError(f"unknown account: {account_id!r}")

    @staticmethod
    def _require_positive(amount):
        if not amount > 0:
            raise ValueError(f"amount must be positive, got {amount!r}")

    def _commit(self, events):
        """Stage ``events`` through the reducer, then publish log and balances together.

        Nothing is published unless every event applies cleanly, so a failure
        leaves both the log and the balances untouched.
        """
        staged = dict(self._balances)
        for event in events:
            staged = apply_event(staged, event)
        self._log.extend(events)
        self._balances = staged

    # ----- commands ---------------------------------------------------------

    def open_account(self, account_id):
        """Open a new account at zero balance. ValueError if it already exists."""
        if account_id in self._balances:
            raise ValueError(f"account already exists: {account_id!r}")
        self._commit([AccountOpened(account_id)])

    def deposit(self, account_id, amount):
        """Add ``amount`` (> 0) to an existing account."""
        self._require_account(account_id)
        self._require_positive(amount)
        self._commit([Deposited(account_id, amount)])

    def withdraw(self, account_id, amount):
        """Remove ``amount`` (> 0); InsufficientFunds if the balance is too low."""
        self._require_account(account_id)
        self._require_positive(amount)
        if self._balances[account_id] < amount:
            raise InsufficientFunds(
                f"balance {self._balances[account_id]} is below {amount}"
            )
        self._commit([Withdrawn(account_id, amount)])

    def transfer(self, src, dst, amount):
        """Move ``amount`` from ``src`` to ``dst`` atomically."""
        self._require_account(src)
        self._require_account(dst)
        self._require_positive(amount)
        if self._balances[src] < amount:
            raise InsufficientFunds(
                f"balance {self._balances[src]} is below {amount}"
            )
        self._commit([Withdrawn(src, amount), Deposited(dst, amount)])

    # ----- queries ----------------------------------------------------------

    def balance(self, account_id):
        """Return the current balance of an existing account."""
        self._require_account(account_id)
        return self._balances[account_id]

    def snapshot(self):
        """Return a copy of the current balances (account id -> balance)."""
        return dict(self._balances)

    def history(self):
        """Return the ordered event log."""
        return list(self._log)

    @classmethod
    def from_history(cls, events):
        """Rebuild a bank by replaying ``events``."""
        bank = cls()
        log = list(events)
        bank._log = log
        bank._balances = replay(log)
        return bank
