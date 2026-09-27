"""Frozen candidate-side probes for hard_oss_v1 ho06-more-itertools-running-statistics
(public task, protocol observe-v1).

Each probe runs the candidate's more_itertools on fixed inputs and reports what
came back. It asserts nothing: the acceptance driver judges the observations
(see ``ormas_probe``). Numbers are encoded by exact type: int/float as
themselves, ``{"F": [n, d]}`` for Fraction, ``{"D": str}`` for Decimal,
``{"C": [re, im]}`` for complex.
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from fractions import Fraction
from itertools import count, islice

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ormas_probe as P  # noqa: E402

ROOT = os.path.dirname(HERE)
mi = None
DATA = [4, 3, 7, 0, 8, 1, 6, 2, 9, 5]
NAMES = ("Stats", "running_min", "running_max", "running_statistics", "running_mean", "running_median")


def setup():
    global mi
    sys.path.insert(0, ROOT)
    import more_itertools as module

    if not os.path.abspath(module.__file__).startswith(os.path.join(ROOT, "more_itertools") + os.sep):
        raise RuntimeError("more_itertools was imported from %s, not the candidate checkout" % module.__file__)
    mi = module


def enc(x):
    kind = type(x)
    if kind in (int, float, str, bool, type(None)):
        return x
    if kind is Fraction:
        return {"F": [x.numerator, x.denominator]}
    if kind is Decimal:
        return {"D": str(x)}
    if kind is complex:
        return {"C": [x.real, x.imag]}
    if kind in (list, tuple):
        return [enc(v) for v in x]
    return {"object": kind.__name__}


WATCH = {"AttributeError": AttributeError, "TypeError": TypeError, "ValueError": ValueError}


def att(thunk):
    """``P.attempt`` that also reports which builtin error classes an exception is an instance of."""
    return P.attempt(thunk, WATCH)


def fn(name):
    return getattr(mi, name)


def run(name, data, **kwargs):
    """Everything the function yields, encoded; or the exception."""
    return att(lambda: [enc(v) for v in fn(name)(data, **kwargs)])


def stats(st):
    return [enc(getattr(st, f)) for f in ("size", "minimum", "median", "maximum", "mean")]


def run_stats(data, **kwargs):
    return att(lambda: [stats(st) for st in fn("running_statistics")(data, **kwargs)])


def random_data(seed, k=400, hi=25):
    """Deterministic data; the driver regenerates it with the same LCG."""
    x, out = seed + 1, []
    for _ in range(k):
        x = (x * 1103515245 + 12345) % 2147483648
        out.append((x >> 8) % hi)
    return out


def probe_exports():
    star = {}
    exec("from more_itertools import *", star)
    return {"attributes": sorted(n for n in NAMES if hasattr(mi, n)), "star": sorted(n for n in NAMES if n in star)}


def probe_running_min_unbounded():
    return {
        "data": run("running_min", DATA), "empty": run("running_min", []),
        "floats": run("running_min", [8.5, 9.5, 7.5, 6.5]),
        "fractions": run("running_min", [Fraction(3, 2), Fraction(1, 2)]),
        "decimals": run("running_min", [Decimal("2.5"), Decimal("3.5")]),
    }


def probe_running_max_unbounded():
    return {
        "data": run("running_max", DATA), "empty": run("running_max", []),
        "floats": run("running_max", [8.5, 9.5, 7.5, 6.5]),
        "decimals": run("running_max", [Decimal("2.5"), Decimal("1.5")]),
    }


def probe_running_min_max_windowed_examples():
    return {"min": run("running_min", DATA, maxlen=3), "max": run("running_max", DATA, maxlen=3)}


def probe_running_min_max_windowed_match_brute_force():
    out = {}
    for seed in range(3):
        data = random_data(seed)
        for maxlen in (2, 3, 4, 5, 7, 16):
            for name in ("running_min", "running_max"):
                out["%s/%d/%d" % (name, seed, maxlen)] = run(name, iter(data), maxlen=maxlen)
    runs = [5, 5, 5, 1, 1, 9, 9, 9, 2, 2, 2, 2]
    for maxlen in (2, 3):
        for name in ("running_min", "running_max"):
            out["%s/runs/%d" % (name, maxlen)] = run(name, runs, maxlen=maxlen)
    return out


def probe_window_of_one_and_window_larger_than_data():
    data = random_data(11, k=60)
    out = {}
    for name in ("running_min", "running_max", "running_mean"):
        out[name] = {"one": run(name, iter(data), maxlen=1), "len": run(name, iter(data), maxlen=len(data)),
                     "ten_times": run(name, iter(data), maxlen=10 * len(data)), "unbounded": run(name, iter(data))}
    return out


def probe_running_mean_windowed():
    xs = [40, 30, 50, 46, 39, 44]
    cs = [3 + 4j, 5 - 1j, 4 + 3j]
    out = {"unbounded": run("running_mean", xs), "window3": run("running_mean", xs, maxlen=3),
           "complex": run("running_mean", cs), "complex2": run("running_mean", cs, maxlen=2)}
    data = random_data(5)
    for maxlen in (2, 3, 5):
        out["random/%d" % maxlen] = run("running_mean", iter(data), maxlen=maxlen)
    return out


def probe_invalid_window_rejected_when_called():
    # Called, never iterated: an error must come from the call itself.
    return {"%s/%d" % (name, bad): att(lambda: type(fn(name)([10, 5, 20], maxlen=bad)).__name__)
            for name in ("running_min", "running_max", "running_mean", "running_statistics") for bad in (0, -1)}


def probe_non_iterable_rejected_when_called():
    return {name: att(lambda: type(fn(name)(None)).__name__)
            for name in ("running_min", "running_max", "running_mean", "running_statistics")}


def probe_outputs_are_streamed():
    def first_stats():
        return stats(next(iter(fn("running_statistics")(count(7)))))

    def no_read_ahead():
        source = iter([3, 1, 2])
        it = fn("running_min")(source, maxlen=2)
        return [enc(next(it)), next(source)]

    return {
        "min_down": att(lambda: [enc(v) for v in islice(fn("running_min")(count(10, -1)), 4)]),
        "max_window": att(lambda: [enc(v) for v in islice(fn("running_max")(count(1), maxlen=2), 4)]),
        "min_window": att(lambda: [enc(v) for v in islice(fn("running_min")(count(1), maxlen=2), 4)]),
        "mean_window": att(lambda: [enc(v) for v in islice(fn("running_mean")(count(1), maxlen=2), 3)]),
        "stats_first": att(first_stats),
        "no_read_ahead": att(no_read_ahead),
    }


def probe_running_statistics_unbounded():
    return {"data": run_stats(iter(DATA)), "empty": run_stats([])}


def probe_running_statistics_windowed():
    return {str(maxlen): run_stats(iter(DATA), maxlen=maxlen) for maxlen in (1, 2, 3, 4)}


def probe_running_statistics_numeric_types():
    out = {}
    for kind in (int, float, Fraction, Decimal):
        for maxlen in (None, 3):
            out["%s/%s" % (kind.__name__, maxlen)] = run_stats(map(kind, DATA), maxlen=maxlen)
    for maxlen in (None, 3):
        out["complex/%s" % maxlen] = run_stats(map(complex, DATA), maxlen=maxlen)
    return out


def probe_running_min_max_reject_complex():
    return {"%s/%s" % (name, maxlen): run(name, map(complex, DATA), maxlen=maxlen)
            for name in ("running_min", "running_max") for maxlen in (None, 3)}


def probe_stats_record():
    def make(*args, **kwargs):
        return fn("Stats")(*args, **kwargs)

    def build():
        st = make(size=5, minimum=0, median=4, maximum=8, mean=4.4)
        return stats(st)

    def setattr_size():
        st = make(size=5, minimum=0, median=4, maximum=8, mean=4.4)
        st.size = 10
        return stats(st)

    kw = dict(size=5, minimum=0, median=4, maximum=8, mean=4.4)
    return {
        "fields": att(build),
        "positional": att(lambda: stats(make(5, 0, 4, 8, 4.4))),
        "equal": att(lambda: make(**kw) == make(**kw)),
        "equal_positional": att(lambda: make(**kw) == make(5, 0, 4, 8, 4.4)),
        "unequal": att(lambda: make(**kw) != make(size=5, minimum=0, median=4, maximum=8, mean=4.5)),
        "hash_equal": att(lambda: hash(make(**kw)) == hash(make(**kw))),
        "dict_key": att(lambda: {make(**kw): 1}[make(5, 0, 4, 8, 4.4)]),
        "assign": att(setattr_size),
        "vars": att(lambda: sorted(vars(make(**kw)))),
        "len": att(lambda: len(make(**kw))),
        "index": att(lambda: enc(make(**kw)[0])),
        "iter": att(lambda: [enc(v) for v in iter(make(**kw))]),
    }


def probe_running_median_unchanged():
    xs = [5.0, 9.0, 4.0, 12.0, 8.0, 9.0]
    return {"unbounded": run("running_median", xs), "window3": run("running_median", xs, maxlen=3),
            "zero": att(lambda: type(fn("running_median")([1], maxlen=0)).__name__)}


PROBES = {name[len("probe_"):]: f for name, f in list(globals().items()) if name.startswith("probe_")}

if __name__ == "__main__":
    P.main(setup, PROBES)
