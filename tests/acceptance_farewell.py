"""Client-owned follow-on acceptance of candidate output."""
import json

from ormas_acceptance import run


def test_farewell_names_trims_and_handles_empty():
    result = run([
        "python3",
        "-c",
        "import json; from sandbox.greet import farewell; "
        "print(json.dumps([farewell('Ormas'), farewell('  Jake '), farewell('')]))",
    ])
    assert result["returncode"] == 0
    assert json.loads(result["output"]) == ["Goodbye, Ormas.", "Goodbye, Jake.", "Goodbye."]
