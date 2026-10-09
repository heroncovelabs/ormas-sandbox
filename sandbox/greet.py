def greet(name: str) -> str:
    return "hello"


def farewell(name: str) -> str:
    trimmed = name.strip()
    if not trimmed:
        return "Goodbye."
    return f"Goodbye, {trimmed}."
