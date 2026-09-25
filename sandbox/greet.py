def greet(name: str) -> str:
    return f"Hello, {name.strip()}."


def farewell(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        return "Goodbye."
    return f"Goodbye, {cleaned}."
