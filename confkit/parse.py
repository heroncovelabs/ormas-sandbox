import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)\Z")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)\Z"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(s):
    """s starts with '"'. Return the decoded string; validate trailing part."""
    out = []
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
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if c == '"':
            break
        out.append(c)
        i += 1
    rest = s[i + 1:].strip()
    if rest and not rest.startswith("#"):
        raise ValueError("unexpected content after quoted value")
    return "".join(out)


def _strip_comment(s):
    for i, c in enumerate(s):
        if c == "#" and (i == 0 or s[i - 1].isspace()):
            return s[:i]
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
        if "=" not in line:
            raise ValueError("line has no '=': %r" % line)
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            raise ValueError("empty key: %r" % line)
        value = value.lstrip()
        if value.startswith('"'):
            result[key] = _parse_quoted(value)
        else:
            value = _strip_comment(value).rstrip()
            result[key] = _coerce(value) if value else ""
    return result
