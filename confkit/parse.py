"""Parser for the VulcanConf configuration format.

See the module docstring of the test suite / issue notes for the full rule
set: line-based ``key = value`` entries, ``#`` comments, double-quoted values
with escapes, and coercion of unquoted values to bool/None/int/float.
"""

import re

# Integer: [+-]?(0|[1-9][0-9]*) -- leading zeros keep the value a string.
_INT_RE = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")

# Float: digits on both sides of the dot (1.5) or an exponent form
# (1e3, 2.5e-2). Bare-dot forms like "5." and ".5" stay strings.
_FLOAT_RE = re.compile(r"[+-]?(?:[0-9]+\.[0-9]+|[0-9]+(?:\.[0-9]+)?[eE][+-]?[0-9]+)")

# Escape sequences recognized inside double-quoted values. Any other
# backslash pair keeps the escaped character and drops the backslash.
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def parse_config(text: str) -> dict:
    """Parse the VulcanConf config format into a dict (later keys win)."""
    result = {}
    for raw_line in text.split("\n"):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue  # blank line or full-line comment
        if "=" not in line:
            raise ValueError("missing '=' in line: %r" % (line,))
        key, _, value_part = line.partition("=")
        key = key.strip()
        if not key:
            raise ValueError("empty key in line: %r" % (line,))
        result[key] = _parse_value(value_part.lstrip())
    return result


def _parse_value(value: str):
    """Parse a value whose leading whitespace has already been stripped."""
    if value.startswith('"'):
        return _parse_quoted(value)

    # Unquoted value: an inline comment begins at the first '#' that is at
    # the start of the value or is preceded by whitespace.
    end = len(value)
    for i, ch in enumerate(value):
        if ch == "#" and (i == 0 or value[i - 1].isspace()):
            end = i
            break
    value = value[:end].rstrip()
    if not value:
        return ""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None
    if _INT_RE.fullmatch(value):
        return int(value)
    if _FLOAT_RE.fullmatch(value):
        return float(value)
    return value


def _parse_quoted(value: str) -> str:
    """Parse a double-quoted value; ``value`` starts with the opening quote."""
    chars = []
    i = 1
    n = len(value)
    while i < n:
        ch = value[i]
        if ch == "\\":
            if i + 1 >= n:
                raise ValueError("missing closing quote in line: %r" % (value,))
            nxt = value[i + 1]
            chars.append(_ESCAPES.get(nxt, nxt))
            i += 2
        elif ch == '"':
            # Only whitespace and/or a '#' comment may follow the quote.
            rest = value[i + 1 :].lstrip()
            if rest and not rest.startswith("#"):
                raise ValueError(
                    "unexpected content after closing quote: %r" % (value,)
                )
            return "".join(chars)
        else:
            chars.append(ch)
            i += 1
    raise ValueError("missing closing quote in line: %r" % (value,))
