"""Ormas public-only Outcomes adapter; no VulcanBench scoring tests.

The sole authored behavior suite is in ormas_acceptance/test_instruction_*.py.
This adapter uses the existing candidate bridge in the external driver and
runs that suite plus pristine public regressions in the candidate. Local
execution uses the same child argv. The exact collected count is derived
from the frozen base suites, not an arbitrary acceptance threshold.
"""

import json
from pathlib import Path
import subprocess
import sys

_PROGRAM = 'import json, pathlib, subprocess, sys, tempfile, xml.etree.ElementTree as ET\nwith tempfile.TemporaryDirectory(prefix="ormas-public-") as directory:\n    report = pathlib.Path(directory) / "result.xml"\n    argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml=" + str(report)] + [\'ormas_acceptance/test_instruction_nx_digraph_node_connectivity.py\', \'networkx/algorithms/connectivity/tests/test_connectivity.py\', \'networkx/algorithms/connectivity/tests/test_cuts.py\']\n    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)\n    outcome = "setup"\n    try:\n        document = ET.parse(report)\n        cases = list(document.iter("testcase"))\n        failures = list(document.iter("failure"))\n        complete = len(cases) == 60 and not list(document.iter("error")) and not list(document.iter("skipped"))\n        if complete and result.returncode == 0 and not failures:\n            outcome = "pass"\n        elif complete and result.returncode == 1 and failures and all(f.get("message", "").startswith(("assert ", "AssertionError")) for f in failures):\n            outcome = "assertion"\n    except (OSError, ET.ParseError):\n        pass\n    print(json.dumps({"outcome": outcome, "output": result.stdout}))\n'


def test_instruction_acceptance_and_pristine_regressions():
    argv = ["python3", "-c", _PROGRAM]
    if Path("/ormas/bridge/socket").exists():
        from ormas_acceptance import run
        observation = run(argv)
        code, output = observation["returncode"], observation["output"]
    else:
        observation = subprocess.run(
            [sys.executable, "-c", _PROGRAM],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        code, output = observation.returncode, observation.stdout
    if code != 0:
        raise RuntimeError("Public verifier process could not run: " + output)
    try:
        result = json.loads(output)
    except (TypeError, ValueError):
        raise RuntimeError("Public verifier produced no structured result: " + output) from None
    if result.get("outcome") not in ("pass", "assertion"):
        raise RuntimeError("Public suite collection/import/execution error: " + result.get("output", ""))
    assert result["outcome"] == "pass", result["output"]
