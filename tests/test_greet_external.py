from ormas_acceptance import run


def test_greet_suite_observes_candidate():
    result = run(["python3", "-m", "pytest", "-q", "tests/test_greet.py"], timeout_s=60)
    assert result["returncode"] == 0, result["output"][-3000:]
