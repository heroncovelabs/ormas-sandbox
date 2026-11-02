import re


_INTEGER = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")
_FLOAT = re.compile(
    r"[+-]?[0-9]+(?:\.[0-9]+(?:[eE][+-]?[0-9]+)?|[eE][+-]?[0-9]+)"
)


def _parse_quoted(value):
    characters = []
    escaped = False
    escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
    for index in range(1, len(value)):
        character = value[index]
        if escaped:
            characters.append(escapes.get(character, character))
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == '"':
            trailing = value[index + 1:].lstrip()
            if trailing and not trailing.startswith("#"):
                raise ValueError("Unexpected content after quoted value")
            return "".join(characters)
        else:
            characters.append(character)
    raise ValueError("Missing closing quote")


def _coerce(value):
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
    """Parse line-based VulcanConf text, with later keys overwriting earlier ones."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError("Expected key = value")
        key = key.strip()
        if not key:
            raise ValueError("Empty key")
        value = value.lstrip()
        if value.startswith('"'):
            result[key] = _parse_quoted(value)
            continue
        for index, character in enumerate(value):
            if character == "#" and (index == 0 or value[index - 1].isspace()):
                value = value[:index]
                break
        result[key] = _coerce(value.rstrip())
    return result
