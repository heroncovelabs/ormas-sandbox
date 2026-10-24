import re

_INT_RE = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)")
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(raw):
    # raw starts with the opening quote
    out = []
    i = 1
    while i < len(raw):
        ch = raw[i]
        if ch == "\\":
            if i + 1 >= len(raw):
                break
            nxt = raw[i + 1]
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if ch == '"':
            rest = raw[i + 1:].lstrip()
            if rest and not rest.startswith("#"):
                raise ValueError("unexpected content after quoted value: %r" % rest)
            return "".join(out)
        out.append(ch)
        i += 1
    raise ValueError("missing closing quote")


def _parse_unquoted(raw):
    for i, ch in enumerate(raw):
        if ch == "#" and (i == 0 or raw[i - 1].isspace()):
            raw = raw[:i]
            break
    value = raw.rstrip()
    if value == "":
        return ""
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("null", "none"):
        return None
    if _INT_RE.fullmatch(value):
        return int(value)
    if _FLOAT_RE.fullmatch(value):
        return float(value)
    return value


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
            raise ValueError("missing '=' in line: %r" % line)
        key, raw = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("empty key in line: %r" % line)
        raw = raw.lstrip()
        if raw.startswith('"'):
            result[key] = _parse_quoted(raw)
        else:
            result[key] = _parse_unquoted(raw)
    return result
