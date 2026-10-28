"""Parser for the VulcanConf line-based config format."""

import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)

_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(s, start):
    """Parse a quoted value beginning at ``start`` (an opening quote).

    Returns ``(value, index_after_closing_quote)``.
    """
    i = start + 1
    out = []
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "\\":
            if i + 1 >= n:
                raise ValueError("dangling escape in quoted value")
            nxt = s[i + 1]
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if ch == '"':
            return "".join(out), i + 1
        out.append(ch)
        i += 1
    raise ValueError("unterminated quoted value")


def _strip_inline_comment(s):
    """Cut an unquoted value at the first '#' at start or preceded by whitespace."""
    for i, ch in enumerate(s):
        if ch == "#" and (i == 0 or s[i - 1].isspace()):
            return s[:i]
    return s


def _coerce(value):
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
    s = raw.lstrip()
    if s.startswith('"'):
        value, end = _parse_quoted(s, 0)
        rest = s[end:]
        stripped = rest.lstrip()
        if stripped and not stripped.startswith("#"):
            raise ValueError("unexpected trailing content after quoted value")
        return value
    return _coerce(_strip_inline_comment(s).rstrip())


def parse_config(text):
    """Parse the VulcanConf config format into a dict (see issue.md)."""
    result = {}
    for raw_line in text.split("\n"):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("missing '=' in line: %r" % (line,))
        key_part, _, value_part = line.partition("=")
        key = key_part.strip()
        if not key:
            raise ValueError("empty key in line: %r" % (line,))
        result[key] = _parse_value(value_part)
    return result
