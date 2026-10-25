"""Parser for the VulcanConf configuration format."""

import re


_INTEGER = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")
_FLOAT = re.compile(
    r"[+-]?(?:"
    r"[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?"
    r"|[0-9]+[eE][+-]?[0-9]+"
    r")"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(value):
    chars = []
    index = 1
    while index < len(value):
        char = value[index]
        if char == '"':
            trailing = value[index + 1 :].lstrip()
            if trailing and not trailing.startswith("#"):
                raise ValueError("unexpected content after quoted value")
            return "".join(chars)
        if char == "\\":
            index += 1
            if index == len(value):
                break
            char = value[index]
            chars.append(_ESCAPES.get(char, char))
        else:
            chars.append(char)
        index += 1
    raise ValueError("unterminated quoted value")


def _parse_unquoted(value):
    for index, char in enumerate(value):
        if char == "#" and (index == 0 or value[index - 1].isspace()):
            value = value[:index]
            break
    value = value.rstrip()
    if not value:
        return ""

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None
    if _INTEGER.fullmatch(value):
        return int(value)
    if _FLOAT.fullmatch(value):
        return float(value)
    return value


def parse_config(text):
    """Parse VulcanConf source into a dict, with later keys taking precedence."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError("expected key = value")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("empty key")
        value = value.lstrip()
        result[key] = (
            _parse_quoted(value) if value.startswith('"') else _parse_unquoted(value)
        )
    return result
