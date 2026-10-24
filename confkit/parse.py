"""Parser for the VulcanConf config format."""

import re

_INT = re.compile(r"[+-]?(0|[1-9][0-9]*)")
_FLOAT = re.compile(r"[+-]?[0-9]+\.[0-9]+|[+-]?[0-9]+(\.[0-9]+)?[eE][+-]?[0-9]+")
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(value):
    chars = []
    i = 1
    while i < len(value):
        c = value[i]
        if c == "\\":
            if i + 1 >= len(value):
                break
            nxt = value[i + 1]
            chars.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if c == '"':
            rest = value[i + 1:].lstrip()
            if rest and not rest.startswith("#"):
                raise ValueError("unexpected content after quoted value")
            return "".join(chars)
        chars.append(c)
        i += 1
    raise ValueError("missing closing quote")


def _strip_comment(value):
    for i, c in enumerate(value):
        if c == "#" and (i == 0 or value[i - 1].isspace()):
            return value[:i].rstrip()
    return value.rstrip()


def _coerce(text):
    if text == "":
        return ""
    lowered = text.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "none"):
        return None
    if _INT.fullmatch(text):
        return int(text)
    if _FLOAT.fullmatch(text):
        return float(text)
    return text


def _parse_value(raw):
    value = raw.lstrip()
    if value.startswith('"'):
        return _parse_quoted(value)
    return _coerce(_strip_comment(value))


def parse_config(text):
    """Parse VulcanConf source into a dict; later keys overwrite earlier ones."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("line has no '=': %r" % line)
        key, raw = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("empty key")
        result[key] = _parse_value(raw)
    return result
