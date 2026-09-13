def greet(name: str) -> str:
    return f"Hello, {name.strip()}."


def farewell(name: str) -> str:
    name = name.strip()
    if not name:
        return "Goodbye."
    return f"Goodbye, {name}."
