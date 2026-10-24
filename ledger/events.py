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
    new_state = dict(state)
    if isinstance(event, AccountOpened):
        if event.account_id in new_state:
            raise ValueError("account already opened: %r" % (event.account_id,))
        new_state[event.account_id] = 0
    elif isinstance(event, Deposited):
        if event.account_id not in new_state:
            raise ValueError("unknown account: %r" % (event.account_id,))
        new_state[event.account_id] += event.amount
    elif isinstance(event, Withdrawn):
        if event.account_id not in new_state:
            raise ValueError("unknown account: %r" % (event.account_id,))
        new_state[event.account_id] -= event.amount
    else:
        raise TypeError("unknown event: %r" % (event,))
    return new_state


def replay(events):
    """Fold a sequence of events from an empty ledger into a balances dict."""
    state = {}
    for event in events:
        state = apply_event(state, event)
    return state
