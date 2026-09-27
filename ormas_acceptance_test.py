"""Ormas external acceptance for ho06-more-itertools-running-statistics (protocol observe-v1).

Generated from manifest.json and fixtures/ho06-more-itertools-running-statistics/acceptance/expectations.py
by build_branches.py; do not edit by hand.

The linux-python-pytest-v1 verifier runs this file in a driver container that
holds no candidate code. Each test asks the verifier bridge to run one frozen
probe from oss_checks/probe_ho06_running_statistics.py inside the isolated candidate container. A probe
concludes nothing: it reports what the candidate's code did (values, exception
types, sequences) as one record tagged with a random nonce drawn here for that
call. Every assertion runs below, in this process. Whatever the candidate does
to its own interpreter (patching a test framework, skipping, exiting early)
cannot become a pass.

Scoring: a probe that could not start (the bridge failed) or reported a setup
error (the package does not import) raises RuntimeError, which the verifier
reports as setup. Everything else is the candidate's and fails by assertion: a
process the candidate ended while being imported, an interrupted probe, missing
or extra records, or observations that differ from the expected behavior.
"""
import json
import secrets

from ormas_acceptance import run

PROBE = 'oss_checks/probe_ho06_running_statistics.py'
TAG = "ORMAS-OBS"


def _observe(name):
    nonce = secrets.token_hex(16)
    result = run(["python3", "-I", PROBE, name, nonce], timeout_s=60)
    code, output = result["returncode"], result["output"]
    records = []
    for line in output.splitlines():
        parts = line.split(" ", 3)
        if len(parts) == 4 and parts[0] == TAG and parts[1] == nonce:
            records.append((parts[2], parts[3]))
    kinds = [kind for kind, _ in records]
    tail = output[-3000:]
    if "ready" not in kinds:
        if kinds != ["begin"]:
            raise RuntimeError("probe %s did not finish setup (records %s, exit %s): %s" % (name, kinds, code, tail))
        raise AssertionError("probe %s: the candidate ended the process while it was imported (exit %s): %s"
                             % (name, code, tail))
    assert kinds == ["begin", "ready", "result"], (
        "probe %s was disturbed: records %s, exit %s: %s" % (name, kinds, code, tail))
    try:
        observed = json.loads(records[2][1])
    except ValueError:
        raise AssertionError("probe %s emitted a malformed result: %s" % (name, tail)) from None
    assert not (isinstance(observed, dict) and "__raised__" in observed), (
        "probe %s was interrupted by the candidate: %r" % (name, observed.get("__raised__")))
    return observed


def _judge(expect, name):
    observed = _observe(name)
    try:
        expect(observed)
    except AssertionError:
        raise
    except Exception as exc:
        raise AssertionError("observations of %s do not have the expected shape (%s: %s): %r"
                             % (name, type(exc).__name__, exc, observed)) from None


# --- expectations: fixtures/ho06-more-itertools-running-statistics/acceptance/expectations.py ---

DATA = [4, 3, 7, 0, 8, 1, 6, 2, 9, 5]
NAMES = ["Stats", "running_max", "running_mean", "running_median", "running_min", "running_statistics"]


def ok(value):
    return {"ok": value}


def raised(record, name, what):
    assert "raised" in record, "%s: expected %s, got %r" % (what, name, record)
    assert name in record.get("isa", []), "%s: expected %s, got %s: %s" % (what, name, record["raised"], record.get("message"))


def F(n, d=1):
    return {"F": [n, d]}


def D(s):
    return {"D": s}


def windows(data, maxlen):
    for end in range(1, len(data) + 1):
        yield data[max(0, end - maxlen):end]


def random_data(seed, k=400, hi=25):
    """The probe's deterministic data (the same LCG)."""
    x, out = seed + 1, []
    for _ in range(k):
        x = (x * 1103515245 + 12345) % 2147483648
        out.append((x >> 8) % hi)
    return out


def mean(window):
    return sum(window) / len(window)


def median(window):
    s, n = sorted(window), len(window)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def stats_of(window):
    return [len(window), min(window), median(window), max(window), mean(window)]


def expect_exports(o):
    assert o == {"attributes": NAMES, "star": NAMES}, o


def expect_running_min_unbounded(o):
    assert o["data"] == ok([4, 3, 3, 0, 0, 0, 0, 0, 0, 0]), o["data"]
    assert o["empty"] == ok([]), o["empty"]
    assert o["floats"] == ok([8.5, 8.5, 7.5, 6.5]), o["floats"]
    assert o["fractions"] == ok([F(3, 2), F(1, 2)]), o["fractions"]
    assert o["decimals"] == ok([D("2.5"), D("2.5")]), o["decimals"]


def expect_running_max_unbounded(o):
    assert o["data"] == ok([4, 4, 7, 7, 8, 8, 8, 8, 9, 9]), o["data"]
    assert o["empty"] == ok([]), o["empty"]
    assert o["floats"] == ok([8.5, 9.5, 9.5, 9.5]), o["floats"]
    assert o["decimals"] == ok([D("2.5"), D("2.5")]), o["decimals"]


def expect_running_min_max_windowed_examples(o):
    assert o["min"] == ok([4, 3, 3, 0, 0, 0, 1, 1, 2, 2]), o["min"]
    assert o["max"] == ok([4, 4, 7, 7, 8, 8, 8, 6, 9, 9]), o["max"]


def expect_running_min_max_windowed_match_brute_force(o):
    for seed in range(3):
        data = random_data(seed)
        for maxlen in (2, 3, 4, 5, 7, 16):
            assert o["running_min/%d/%d" % (seed, maxlen)] == ok([min(w) for w in windows(data, maxlen)]), (seed, maxlen)
            assert o["running_max/%d/%d" % (seed, maxlen)] == ok([max(w) for w in windows(data, maxlen)]), (seed, maxlen)
    runs = [5, 5, 5, 1, 1, 9, 9, 9, 2, 2, 2, 2]
    for maxlen in (2, 3):
        assert o["running_min/runs/%d" % maxlen] == ok([min(w) for w in windows(runs, maxlen)]), maxlen
        assert o["running_max/runs/%d" % maxlen] == ok([max(w) for w in windows(runs, maxlen)]), maxlen


def expect_window_of_one_and_window_larger_than_data(o):
    data = random_data(11, k=60)
    expected = {"running_min": [min(w) for w in windows(data, len(data))],
                "running_max": [max(w) for w in windows(data, len(data))],
                "running_mean": [mean(w) for w in windows(data, len(data))]}
    for name, r in o.items():
        assert r["one"] == ok([float(v) for v in data] if name == "running_mean" else data), name
        assert r["unbounded"] == ok(expected[name]), (name, r["unbounded"])
        assert r["len"] == r["unbounded"] and r["ten_times"] == r["unbounded"], name
    assert sorted(o) == ["running_max", "running_mean", "running_min"]


def expect_running_mean_windowed(o):
    assert o["unbounded"] == ok([40.0, 35.0, 40.0, 41.5, 41.0, 41.5]), o["unbounded"]
    assert o["window3"] == ok([40.0, 35.0, 40.0, 42.0, 45.0, 43.0]), o["window3"]
    C = lambda z: {"C": [z.real, z.imag]}  # noqa: E731
    assert o["complex"] == ok([C(3 + 4j), C(4 + 1.5j), C(4 + 2j)]), o["complex"]
    assert o["complex2"] == ok([C(3 + 4j), C(4 + 1.5j), C(4.5 + 1j)]), o["complex2"]
    data = random_data(5)
    for maxlen in (2, 3, 5):
        assert o["random/%d" % maxlen] == ok([mean(w) for w in windows(data, maxlen)]), maxlen


def expect_invalid_window_rejected_when_called(o):
    assert len(o) == 8, o
    for key, r in o.items():
        raised(r, "ValueError", key)


def expect_non_iterable_rejected_when_called(o):
    assert sorted(o) == ["running_max", "running_mean", "running_min", "running_statistics"], o
    for key, r in o.items():
        raised(r, "TypeError", key)


def expect_outputs_are_streamed(o):
    assert o["min_down"] == ok([10, 9, 8, 7]), o["min_down"]
    assert o["max_window"] == ok([1, 2, 3, 4]), o["max_window"]
    assert o["min_window"] == ok([1, 1, 2, 3]), o["min_window"]
    assert o["mean_window"] == ok([1.0, 1.5, 2.5]), o["mean_window"]
    assert o["stats_first"] == ok([1, 7, 7, 7, 7.0]), o["stats_first"]
    assert o["no_read_ahead"] == ok([3, 1]), o["no_read_ahead"]


def expect_running_statistics_unbounded(o):
    assert o["data"] == ok([stats_of(DATA[:i + 1]) for i in range(len(DATA))]), o["data"]
    assert o["data"]["ok"][:2] == [[1, 4, 4, 4, 4.0], [2, 3, 3.5, 4, 3.5]]
    assert o["empty"] == ok([]), o["empty"]


def expect_running_statistics_windowed(o):
    for maxlen in (1, 2, 3, 4):
        assert o[str(maxlen)] == ok([stats_of(w) for w in windows(DATA, maxlen)]), (maxlen, o[str(maxlen)])
    assert o["3"]["ok"][3] == [3, 0, 3, 7, 10 / 3] and o["3"]["ok"][4] == [3, 0, 7, 8, 5.0]


def expect_running_statistics_numeric_types(o):
    for maxlen in ("None", "3"):
        for kind in ("int", "float", "Fraction", "Decimal"):
            r = o["%s/%s" % (kind, maxlen)]
            assert "ok" in r and len(r["ok"]) == len(DATA), (kind, maxlen, r)
            last = r["ok"][-1]
            nine = {"int": 9, "float": 9.0, "Fraction": F(9), "Decimal": D("9")}[kind]
            assert last[3] == nine, (kind, maxlen, last)
        raised(o["complex/%s" % maxlen], "TypeError", "complex/%s" % maxlen)
    assert o["Fraction/None"]["ok"][1][4] == F(7, 2), o["Fraction/None"]["ok"][1]
    assert o["int/None"]["ok"][-1] == stats_of(DATA)


def expect_running_min_max_reject_complex(o):
    assert sorted(o) == ["running_max/3", "running_max/None", "running_min/3", "running_min/None"], o
    for key, r in o.items():
        raised(r, "TypeError", key)


def expect_stats_record(o):
    fields = [5, 0, 4, 8, 4.4]
    assert o["fields"] == ok(fields) and o["positional"] == ok(fields), (o["fields"], o["positional"])
    for key in ("equal", "equal_positional", "unequal", "hash_equal"):
        assert o[key] == ok(True), (key, o[key])
    assert o["dict_key"] == ok(1), o["dict_key"]
    raised(o["assign"], "AttributeError", "assignment")
    for key in ("vars", "len", "index", "iter"):
        raised(o[key], "TypeError", key)


def expect_running_median_unchanged(o):
    assert o["unbounded"] == ok([5.0, 7.0, 5.0, 7.0, 8.0, 8.5]), o["unbounded"]
    assert o["window3"] == ok([5.0, 7.0, 5.0, 9.0, 8.0, 9.0]), o["window3"]
    raised(o["zero"], "ValueError", "maxlen=0")


def test_f2p_exports():
    _judge(expect_exports, 'exports')


def test_f2p_running_min_unbounded():
    _judge(expect_running_min_unbounded, 'running_min_unbounded')


def test_f2p_running_max_unbounded():
    _judge(expect_running_max_unbounded, 'running_max_unbounded')


def test_f2p_running_min_max_windowed_examples():
    _judge(expect_running_min_max_windowed_examples, 'running_min_max_windowed_examples')


def test_f2p_running_min_max_windowed_match_brute_force():
    _judge(expect_running_min_max_windowed_match_brute_force, 'running_min_max_windowed_match_brute_force')


def test_f2p_window_of_one_and_window_larger_than_data():
    _judge(expect_window_of_one_and_window_larger_than_data, 'window_of_one_and_window_larger_than_data')


def test_f2p_running_mean_windowed():
    _judge(expect_running_mean_windowed, 'running_mean_windowed')


def test_f2p_invalid_window_rejected_when_called():
    _judge(expect_invalid_window_rejected_when_called, 'invalid_window_rejected_when_called')


def test_f2p_non_iterable_rejected_when_called():
    _judge(expect_non_iterable_rejected_when_called, 'non_iterable_rejected_when_called')


def test_f2p_outputs_are_streamed():
    _judge(expect_outputs_are_streamed, 'outputs_are_streamed')


def test_f2p_running_statistics_unbounded():
    _judge(expect_running_statistics_unbounded, 'running_statistics_unbounded')


def test_f2p_running_statistics_windowed():
    _judge(expect_running_statistics_windowed, 'running_statistics_windowed')


def test_f2p_running_statistics_numeric_types():
    _judge(expect_running_statistics_numeric_types, 'running_statistics_numeric_types')


def test_f2p_running_min_max_reject_complex():
    _judge(expect_running_min_max_reject_complex, 'running_min_max_reject_complex')


def test_f2p_stats_record():
    _judge(expect_stats_record, 'stats_record')


def test_p2p_running_median_unchanged():
    _judge(expect_running_median_unchanged, 'running_median_unchanged')
