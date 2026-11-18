import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)\Z")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)\Z"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(s):
    """Parse a quoted value starting at s[0] == '"'. Returns the string."""
    buf = []
    i = 1
    n = len(s)
    while True:
        if i >= n:
            raise ValueError("unterminated quoted value")
        c = s[i]
        if c == "\\":
            if i + 1 >= n:
                raise ValueError("unterminated quoted value")
            nxt = s[i + 1]
            buf.append(_ESCAPES.get(nxt, nxt))
            i += 2
        elif c == '"':
            i += 1
            break
        else:
            buf.append(c)
            i += 1
    rest = s[i:]
    if rest.strip() and not rest.lstrip().startswith("#"):
        raise ValueError("unexpected content after quoted value")
    return "".join(buf)


def _strip_comment(s):
    for j, c in enumerate(s):
        if c == "#" and (j == 0 or s[j - 1].isspace()):
            return s[:j]
    return s


def _coerce(s):
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none"):
        return None
    if _INT_RE.match(s):
        return int(s)
    if _FLOAT_RE.match(s):
        return float(s)
    return s


def parse_config(text):
    """Parse the VulcanConf config format into a dict (see issue.md)."""
    result = {}
    for raw in text.split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        idx = line.find("=")
        if idx < 0:
            raise ValueError("line has no '=': %r" % line)
        key = line[:idx].strip()
        if not key:
            raise ValueError("empty key: %r" % line)
        value_part = line[idx + 1:].lstrip()
        if value_part.startswith('"'):
            value = _parse_quoted(value_part)
        else:
            value = _strip_comment(value_part).rstrip()
            value = "" if value == "" else _coerce(value)
        result[key] = value
    return result
