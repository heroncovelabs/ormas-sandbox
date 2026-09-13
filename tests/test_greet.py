from sandbox.greet import greet


def test_greet_names_the_person():
    assert greet("Ormas") == "Hello, Ormas."


def test_greet_strips_whitespace():
    assert greet("  Jake ") == "Hello, Jake."
