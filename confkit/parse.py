import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(raw):
    """Parse a quoted value starting at raw[0] == '"'. Returns the string."""
    out = []
    i = 1
    n = len(raw)
    while True:
        if i >= n:
            raise ValueError("unterminated quoted value")
        ch = raw[i]
        if ch == "\\":
            if i + 1 >= n:
                raise ValueError("unterminated quoted value")
            nxt = raw[i + 1]
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if ch == '"':
            break
        out.append(ch)
        i += 1

    rest = raw[i + 1:].strip()
    if rest and not rest.startswith("#"):
        raise ValueError("invalid content after closing quote")
    return "".join(out)


def _parse_unquoted(raw):
    """Parse an unquoted value, removing inline comments and coercing type."""
    idx = None
    for i, ch in enumerate(raw):
        if ch == "#" and (i == 0 or raw[i - 1].isspace()):
            idx = i
            break
    if idx is not None:
        raw = raw[:idx]
    value = raw.rstrip()

    if value == "":
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


def _parse_value(raw):
    if raw.startswith('"'):
        return _parse_quoted(raw)
    return _parse_unquoted(raw)


def parse_config(text):
    """Parse the VulcanConf config format into a dict (see issue.md)."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("malformed assignment: %r" % line)
        key, _, rest = line.partition("=")
        key = key.strip()
        if key == "":
            raise ValueError("empty key")
        result[key] = _parse_value(rest.lstrip())
    return result
