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

    def _record(self, *events):
        """Apply the entire event batch before publishing its log and balances."""
        balances = self._balances
        for event in events:
            balances = apply_event(balances, event)
        self._log.extend(events)
        self._balances = balances

    def _validate(self, amount, *account_ids):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        for account_id in account_ids:
            if account_id not in self._balances:
                raise ValueError(f"Unknown account: {account_id}")

    def open_account(self, account_id):
        """Open a new account at zero balance. ValueError if it already exists."""
        if account_id in self._balances:
            raise ValueError(f"Account already exists: {account_id}")
        self._record(AccountOpened(account_id))

    def deposit(self, account_id, amount):
        """Add ``amount`` (> 0) to an existing account."""
        self._validate(amount, account_id)
        self._record(Deposited(account_id, amount))

    def withdraw(self, account_id, amount):
        """Remove ``amount`` (> 0); InsufficientFunds if the balance is too low."""
        self._validate(amount, account_id)
        if self._balances[account_id] < amount:
            raise InsufficientFunds(f"Insufficient funds in account: {account_id}")
        self._record(Withdrawn(account_id, amount))

    def transfer(self, src, dst, amount):
        """Move ``amount`` from ``src`` to ``dst`` atomically."""
        self._validate(amount, src, dst)
        if self._balances[src] < amount:
            raise InsufficientFunds(f"Insufficient funds in account: {src}")
        self._record(Withdrawn(src, amount), Deposited(dst, amount))

    def balance(self, account_id):
        """Return the current balance of an existing account."""
        if account_id not in self._balances:
            raise ValueError(f"Unknown account: {account_id}")
        return self._balances[account_id]

    def snapshot(self):
        """Return a copy of the current balances (account id -> balance)."""
        return self._balances.copy()

    def history(self):
        """Return a copy of the ordered event log."""
        return self._log.copy()

    @classmethod
    def from_history(cls, events):
        """Rebuild a bank by replaying ``events``."""
        bank = cls()
        bank._log = list(events)
        bank._balances = replay(bank._log)
        return bank
