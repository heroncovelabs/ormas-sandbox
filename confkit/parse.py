"""VulcanConf parser: line-based key/value config with quoting and type coercion."""

import re

_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
_INT = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")
_FLOAT = re.compile(
    r"[+-]?[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?"
    r"|[+-]?[0-9]+[eE][+-]?[0-9]+"
)


def parse_config(text):
    """Parse VulcanConf source into a dict; later keys overwrite earlier ones."""
    result = {}
    for raw in text.split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("missing '=' in line: %r" % line)
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            raise ValueError("empty key in line: %r" % line)
        result[key] = _parse_value(value.lstrip())
    return result


def _parse_value(value):
    if value.startswith('"'):
        return _parse_quoted(value)
    return _parse_unquoted(value)


def _parse_quoted(value):
    chars = []
    i = 1
    while i < len(value):
        ch = value[i]
        if ch == "\\":
            if i + 1 >= len(value):
                break
            nxt = value[i + 1]
            chars.append(_ESCAPES.get(nxt, nxt))
            i += 2
            continue
        if ch == '"':
            rest = value[i + 1:].lstrip()
            if rest and not rest.startswith("#"):
                raise ValueError("unexpected content after quoted value: %r" % rest)
            return "".join(chars)
        chars.append(ch)
        i += 1
    raise ValueError("unterminated quoted value: %r" % value)


def _parse_unquoted(value):
    cut = len(value)
    for i, ch in enumerate(value):
        if ch == "#" and (i == 0 or value[i - 1].isspace()):
            cut = i
            break
    text = value[:cut].rstrip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None
    if _INT.fullmatch(text):
        return int(text)
    if _FLOAT.fullmatch(text):
        return float(text)
    return text
