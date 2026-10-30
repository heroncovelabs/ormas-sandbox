import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(s):
    """Parse a quoted value starting at s[0] == '"'. Returns the string."""
    buf = []
    i = 1
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            nxt = s[i + 1]
            buf.append(_ESCAPES.get(nxt, nxt))
            i += 2
        elif c == '"':
            break
        else:
            buf.append(c)
            i += 1
    else:
        raise ValueError("unterminated quoted value")

    rest = s[i + 1:]
    stripped = rest.strip()
    if stripped and not stripped.startswith("#"):
        raise ValueError("invalid content after closing quote")
    return "".join(buf)


def _parse_unquoted(v):
    """Parse an unquoted value (already leading-stripped)."""
    for i, c in enumerate(v):
        if c == "#" and (i == 0 or v[i - 1].isspace()):
            v = v[:i]
            break
    v = v.rstrip()
    if v == "":
        return ""

    lowered = v.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None
    if _INT_RE.fullmatch(v):
        return int(v)
    if _FLOAT_RE.fullmatch(v):
        return float(v)
    return v


def parse_config(text):
    """Parse the VulcanConf config format into a dict (see issue.md)."""
    result = {}
    for raw in text.split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw
        stripped = line.strip()
        if not stripped or stripped[0] == "#":
            continue

        if "=" not in line:
            raise ValueError(f"malformed line (no '='): {line!r}")
        key, _, rest = line.partition("=")
        key = key.strip()
        if not key:
            raise ValueError(f"empty key in line: {line!r}")

        value = rest.lstrip()
        if value.startswith('"'):
            result[key] = _parse_quoted(value)
        else:
            result[key] = _parse_unquoted(value)
    return result
