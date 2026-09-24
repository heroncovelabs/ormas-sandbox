"""Client-owned acceptance of candidate output in the declared Ormas profile."""
import json

from ormas_acceptance import run


def test_greet_names_and_trims():
    result = run([
        "python3",
        "-c",
        "import json; from sandbox.greet import greet; "
        "print(json.dumps([greet('Ormas'), greet('  Jake ')]))",
    ])
    assert result["returncode"] == 0
    assert json.loads(result["output"]) == ["Hello, Ormas.", "Hello, Jake."]
