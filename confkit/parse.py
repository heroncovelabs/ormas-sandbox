"""Parser for the VulcanConf configuration format."""

import re


_INTEGER_RE = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")
_FLOAT_RE = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?"
    r"|[0-9]+[eE][+-]?[0-9]+)"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(value):
    """Parse a value whose first character is a double quote."""
    result = []
    index = 1
    while index < len(value):
        char = value[index]
        if char == '"':
            trailing = value[index + 1 :].lstrip()
            if trailing and not trailing.startswith("#"):
                raise ValueError("unexpected content after quoted value")
            return "".join(result)
        if char == "\\":
            index += 1
            if index == len(value):
                break
            char = value[index]
            result.append(_ESCAPES.get(char, char))
        else:
            result.append(char)
        index += 1
    raise ValueError("unterminated quoted value")


def _coerce(value):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None
    if _INTEGER_RE.fullmatch(value):
        return int(value)
    if _FLOAT_RE.fullmatch(value):
        return float(value)
    return value


def _parse_unquoted(value):
    for index, char in enumerate(value):
        if char == "#" and (index == 0 or value[index - 1].isspace()):
            value = value[:index]
            break
    value = value.rstrip()
    return _coerce(value) if value else ""


def parse_config(text):
    """Parse VulcanConf source into a dict, with later keys taking precedence."""
    result = {}
    for raw_line in text.split("\n"):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("expected key = value")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("empty key")
        value = value.lstrip()
        if value.startswith('"'):
            result[key] = _parse_quoted(value)
        else:
            result[key] = _parse_unquoted(value)
    return result
