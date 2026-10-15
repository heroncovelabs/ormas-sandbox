import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(s):
    """s starts with '"'. Return the decoded string or raise ValueError."""
    out = []
    i = 1
    n = len(s)
    while True:
        if i >= n:
            raise ValueError("missing closing quote")
        ch = s[i]
        if ch == "\\":
            if i + 1 >= n:
                raise ValueError("missing closing quote")
            nxt = s[i + 1]
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
        elif ch == '"':
            i += 1
            break
        else:
            out.append(ch)
            i += 1
    rest = s[i:].lstrip()
    if rest and not rest.startswith("#"):
        raise ValueError("unexpected content after quoted value")
    return "".join(out)


def _strip_comment(s):
    for i, ch in enumerate(s):
        if ch == "#" and (i == 0 or s[i - 1].isspace()):
            return s[:i]
    return s


def _coerce(s):
    if s == "":
        return ""
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none"):
        return None
    if _INT_RE.fullmatch(s):
        return int(s)
    if _FLOAT_RE.fullmatch(s):
        return float(s)
    return s


def parse_config(text):
    """Parse the VulcanConf config format into a dict (see issue.md)."""
    result = {}
    for raw in text.split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("line has no '=': %r" % line)
        key, _, value = line.partition("=")
        key = key.strip()
        if key == "":
            raise ValueError("empty key")
        value = value.lstrip()
        if value.startswith('"'):
            result[key] = _parse_quoted(value)
        else:
            result[key] = _coerce(_strip_comment(value).rstrip())
    return result
