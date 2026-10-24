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

    def _stage(self, balances, events):
        """Apply ``events`` to a copy of ``balances`` through the reducer."""
        staged = balances
        for event in events:
            staged = apply_event(staged, event)
        return staged

    def _commit(self, events, balances):
        """Append an already-validated, already-applied event batch."""
        self._log.extend(events)
        self._balances = balances

    @staticmethod
    def _check_amount(amount):
        if amount <= 0:
            raise ValueError("amount must be positive")

    def _check_account(self, account_id):
        if account_id not in self._balances:
            raise ValueError(f"unknown account: {account_id!r}")

    def open_account(self, account_id):
        """Open a new account at zero balance. ValueError if it already exists."""
        if account_id in self._balances:
            raise ValueError(f"account already exists: {account_id!r}")
        events = [AccountOpened(account_id)]
        self._commit(events, self._stage(self._balances, events))

    def deposit(self, account_id, amount):
        """Add ``amount`` (> 0) to an existing account."""
        self._check_account(account_id)
        self._check_amount(amount)
        events = [Deposited(account_id, amount)]
        self._commit(events, self._stage(self._balances, events))

    def withdraw(self, account_id, amount):
        """Remove ``amount`` (> 0); InsufficientFunds if the balance is too low."""
        self._check_account(account_id)
        self._check_amount(amount)
        if self._balances[account_id] < amount:
            raise InsufficientFunds(
                f"balance {self._balances[account_id]} < {amount} for {account_id!r}"
            )
        events = [Withdrawn(account_id, amount)]
        self._commit(events, self._stage(self._balances, events))

    def transfer(self, src, dst, amount):
        """Move ``amount`` from ``src`` to ``dst`` atomically."""
        self._check_account(src)
        self._check_account(dst)
        self._check_amount(amount)
        if self._balances[src] < amount:
            raise InsufficientFunds(
                f"balance {self._balances[src]} < {amount} for {src!r}"
            )
        events = [Withdrawn(src, amount), Deposited(dst, amount)]
        # Stage both reducer applications before committing either event.
        staged = self._stage(self._balances, events)
        self._commit(events, staged)

    def balance(self, account_id):
        """Return the current balance of an existing account."""
        self._check_account(account_id)
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
        events = list(events)
        bank = cls()
        bank._balances = replay(events)
        bank._log = events
        return bank
