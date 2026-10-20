import re

_INT_RE = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)
_QUOTE_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(value):
    """Parse a quoted value starting at value[0] == '"'. Returns the string."""
    chars = []
    i = 1
    n = len(value)
    while i < n:
        c = value[i]
        if c == "\\":
            if i + 1 >= n:
                raise ValueError("unterminated quoted value")
            nxt = value[i + 1]
            chars.append(_QUOTE_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if c == '"':
            rest = value[i + 1:].lstrip()
            if rest and not rest.startswith("#"):
                raise ValueError("invalid content after closing quote")
            return "".join(chars)
        chars.append(c)
        i += 1
    raise ValueError("unterminated quoted value")


def _strip_comment(value):
    """Remove an unquoted inline comment and trailing whitespace."""
    for i, c in enumerate(value):
        if c == "#" and (i == 0 or value[i - 1].isspace()):
            value = value[:i]
            break
    return value.rstrip()


def _coerce(value):
    """Coerce an unquoted, comment-free value to its typed form."""
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
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
    return _coerce(_strip_comment(raw))


def parse_config(text):
    """Parse VulcanConf text into a dict, with later keys overwriting earlier ones."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        key, separator, raw = line.partition("=")
        if not separator:
            raise ValueError(f"malformed line (no '='): {line!r}")
        key = key.strip()
        if not key:
            raise ValueError(f"empty key in line: {line!r}")
        result[key] = _parse_value(raw.lstrip())
    return result
