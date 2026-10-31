import re

_INT_RE = re.compile(r"[+-]?(0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(value):
    """Parse a quoted value starting at value[0] == '"'. Returns a str."""
    out = []
    i = 1
    n = len(value)
    while i < n:
        c = value[i]
        if c == "\\":
            if i + 1 >= n:
                break
            nxt = value[i + 1]
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if c == '"':
            rest = value[i + 1:]
            stripped = rest.lstrip()
            if stripped and not stripped.startswith("#"):
                raise ValueError("unexpected content after quoted value: %r" % rest)
            return "".join(out)
        out.append(c)
        i += 1
    raise ValueError("missing closing quote in value: %r" % value)


def _strip_comment(value):
    """Remove an inline comment from an unquoted value and trailing whitespace."""
    for i, c in enumerate(value):
        if c == "#" and (i == 0 or value[i - 1].isspace()):
            value = value[:i]
            break
    return value.rstrip()


def _coerce(text):
    """Coerce an unquoted, comment-free value to its typed form."""
    if text == "":
        return ""
    lower = text.lower()
    if lower in ("true", "false"):
        return lower == "true"
    if lower in ("null", "none"):
        return None
    if _INT_RE.fullmatch(text):
        return int(text)
    if _FLOAT_RE.fullmatch(text):
        return float(text)
    return text


def _parse_value(raw):
    value = raw.lstrip()
    if value.startswith('"'):
        return _parse_quoted(value)
    return _coerce(_strip_comment(value))


def parse_config(text):
    """Parse VulcanConf into a dict, with later keys overwriting earlier ones."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        key, separator, raw = line.partition("=")
        if not separator:
            raise ValueError("missing '=' in line: %r" % line)
        key = key.strip()
        if not key:
            raise ValueError("empty key in line: %r" % line)
        result[key] = _parse_value(raw)
    return result
