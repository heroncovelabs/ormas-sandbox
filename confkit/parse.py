import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)\Z")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+|[0-9]+(?:\.[0-9]+)?[eE][+-]?[0-9]+)\Z"
)

_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(text):
    """Parse a quoted value from ``text`` (which begins with a quote).

    Returns the unescaped string content. Raises ValueError on malformed
    input.
    """
    chars = []
    i = 1
    length = len(text)
    while i < length:
        ch = text[i]
        if ch == "\\":
            if i + 1 >= length:
                raise ValueError("unterminated quoted value")
            nxt = text[i + 1]
            chars.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if ch == '"':
            rest = text[i + 1:]
            stripped = rest.lstrip()
            if stripped and not stripped.startswith("#"):
                raise ValueError(
                    "unexpected content after closing quote: %r" % rest
                )
            return "".join(chars)
        chars.append(ch)
        i += 1
    raise ValueError("unterminated quoted value")


def _strip_inline_comment(value):
    for idx, ch in enumerate(value):
        if ch == "#" and (idx == 0 or value[idx - 1].isspace()):
            return value[:idx]
    return value


def _coerce(value):
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "none"):
        return None
    if _INT_RE.match(value):
        return int(value)
    if _FLOAT_RE.match(value):
        return float(value)
    return value


def _parse_value(raw):
    value = raw.lstrip()
    if value.startswith('"'):
        return _parse_quoted(value)
    return _coerce(_strip_inline_comment(value).rstrip())


def parse_config(text):
    """Parse the VulcanConf config format into a dict (see issue.md)."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("line has no '=': %r" % line)
        raw_key, raw_value = line.split("=", 1)
        key = raw_key.strip()
        if not key:
            raise ValueError("empty key in line: %r" % line)
        result[key] = _parse_value(raw_value)
    return result
