def greet(name: str) -> str:
    name = name.strip()
    if name:
        return f"Hello, {name}."
    return "Hello."


def farewell(name: str) -> str:
    name = name.strip()
    if name:
        return f"Goodbye, {name}."
    return "Goodbye."
