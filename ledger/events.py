"""The event schema and the pure reducer that folds events into balances.

This is the shared contract with ``ledger/bank.py``: the bank emits these events,
and ``apply_event`` / ``replay`` are the only places that interpret them. Events
are immutable facts; replaying the same log must always reproduce the same state.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AccountOpened:
    account_id: str


@dataclass(frozen=True)
class Deposited:
    account_id: str
    amount: int


@dataclass(frozen=True)
class Withdrawn:
    account_id: str
    amount: int


def apply_event(state, event):
    """Return a new balances dict with ``event`` applied to ``state``.

    ``state`` maps account id -> balance and must not be mutated.
    """
    balances = state.copy()
    if isinstance(event, AccountOpened):
        balances[event.account_id] = 0
    elif isinstance(event, Deposited):
        balances[event.account_id] += event.amount
    elif isinstance(event, Withdrawn):
        balances[event.account_id] -= event.amount
    else:
        raise TypeError(f"Unknown event type: {type(event).__name__}")
    return balances


def replay(events):
    """Fold a sequence of events from an empty ledger into a balances dict."""
    balances = {}
    for event in events:
        balances = apply_event(balances, event)
    return balances
