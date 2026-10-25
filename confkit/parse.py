import re


_INTEGER = re.compile(r"[+-]?(?:0|[1-9][0-9]*)")
_FLOAT = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def _parse_value(value):
    value = value.lstrip()
    if value.startswith('"'):
        characters = []
        index = 1
        while index < len(value):
            character = value[index]
            if character == '"':
                trailing = value[index + 1:].lstrip()
                if trailing and not trailing.startswith("#"):
                    raise ValueError("Unexpected content after quoted value")
                return "".join(characters)
            if character == "\\":
                index += 1
                if index == len(value):
                    break
                character = _ESCAPES.get(value[index], value[index])
            characters.append(character)
            index += 1
        raise ValueError("Missing closing quote")

    for index, character in enumerate(value):
        if character == "#" and (index == 0 or value[index - 1].isspace()):
            value = value[:index]
            break
    value = value.rstrip()
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "none"):
        return None
    if _INTEGER.fullmatch(value):
        return int(value)
    if _FLOAT.fullmatch(value):
        return float(value)
    return value


def parse_config(text):
    """Parse line-based VulcanConf text, with later keys taking precedence."""
    config = {}
    for line_number, line in enumerate(text.split("\n"), start=1):
        line = line.removesuffix("\r")
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Missing '=' on line {line_number}")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Empty key on line {line_number}")
        config[key] = _parse_value(value)
    return config
