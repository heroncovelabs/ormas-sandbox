import re


_INTEGER = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")
_FLOAT = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_quoted(value, line_number):
    characters = []
    index = 1
    while index < len(value):
        character = value[index]
        if character == '"':
            remainder = value[index + 1 :].lstrip()
            if remainder and not remainder.startswith("#"):
                raise ValueError(f"Invalid content after quoted value on line {line_number}")
            return "".join(characters)
        if character == "\\":
            index += 1
            if index == len(value):
                break
            character = _ESCAPES.get(value[index], value[index])
        characters.append(character)
        index += 1
    raise ValueError(f"Unterminated quoted value on line {line_number}")


def _parse_unquoted(value):
    for index, character in enumerate(value):
        if character == "#" and (index == 0 or value[index - 1].isspace()):
            value = value[:index]
            break
    value = value.rstrip()
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
    """Parse VulcanConf source into a dictionary of configuration values."""
    result = {}
    for line_number, line in enumerate(text.split("\n"), start=1):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue

        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError(f"Missing assignment on line {line_number}")
        key = key.strip()
        if not key:
            raise ValueError(f"Empty key on line {line_number}")

        value = value.lstrip()
        if value.startswith('"'):
            result[key] = _parse_quoted(value, line_number)
        else:
            result[key] = _parse_unquoted(value)
    return result
