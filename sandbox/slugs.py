import re


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def truncate_words(text: str, n: int) -> str:
    if n <= 0:
        return ""
    return " ".join(text.split()[:n])
