import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(
    r"[+-]?([0-9]+[.][0-9]+([eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)

_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(text):
    """Parse a value whose first character is a double quote."""
    chars = []
    i = 1
    n = len(text)
    closed = False
    while i < n:
        c = text[i]
        if c == "\\":
            if i + 1 >= n:
                raise ValueError("unterminated escape sequence")
            esc = text[i + 1]
            chars.append(_ESCAPES.get(esc, esc))
            i += 2
            continue
        if c == '"':
            closed = True
            i += 1
            break
        chars.append(c)
        i += 1

    if not closed:
        raise ValueError("missing closing quote")

    rest = text[i:].lstrip()
    if rest and not rest.startswith("#"):
        raise ValueError("unexpected content after quoted value")

    return "".join(chars)


def _strip_inline_comment(text):
    for i, c in enumerate(text):
        if c == "#" and (i == 0 or text[i - 1].isspace()):
            return text[:i]
    return text


def _coerce(text):
    if text == "":
        return ""
    low = text.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none"):
        return None
    if _INT_RE.fullmatch(text):
        return int(text)
    if _FLOAT_RE.fullmatch(text):
        return float(text)
    return text


def _parse_value(raw):
    raw = raw.lstrip()
    if raw.startswith('"'):
        return _parse_quoted(raw)
    return _coerce(_strip_inline_comment(raw).rstrip())


def parse_config(text):
    """Parse the VulcanConf config format into a dict (see issue.md)."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("line has no '=': %r" % (line,))
        key, _, raw = line.partition("=")
        key = key.strip()
        if not key:
            raise ValueError("empty key in line: %r" % (line,))
        result[key] = _parse_value(raw)
    return result
