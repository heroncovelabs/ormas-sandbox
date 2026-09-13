from sandbox.greet import farewell


def test_farewell_names_the_person():
    assert farewell("Ormas") == "Goodbye, Ormas."


def test_farewell_strips_whitespace_and_handles_empty():
    assert farewell("  Jake ") == "Goodbye, Jake."
    assert farewell("") == "Goodbye."
