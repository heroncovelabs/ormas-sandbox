def greet(name: str) -> str:
    return "hello"


def farewell(name: str) -> str:
    name = name.strip()
    if not name:
        return "Goodbye."
    return f"Goodbye, {name}."
