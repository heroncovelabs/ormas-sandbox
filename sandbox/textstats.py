"""Pure text statistics for whitespace-separated tokens."""


def word_count(text: str) -> int:
    return len(text.split())


def longest_word(text: str) -> str:
    return max((token.strip(".,!?;:") for token in text.split()), key=len, default="")


def frequencies(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in text.split():
        word = token.strip(".,!?;:").lower()
        if word:
            counts[word] = counts.get(word, 0) + 1
    return counts
