def greet(name: str) -> str:
    return f"Hello, {name.strip()}."


def farewell(name: str) -> str:
    name = name.strip()
    return f"Goodbye, {name}." if name else "Goodbye."


def shout(text: str) -> str:
    text = " ".join(text.upper().split())
    return text if text.endswith("!") else text + "!"
