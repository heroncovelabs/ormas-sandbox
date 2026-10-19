import re


def parse_config(text):
    """Parse VulcanConf assignments, comments, and scalar values."""
    result = {}
    escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}

    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        stripped_line = line.lstrip()
        if not stripped_line or stripped_line.startswith("#"):
            continue

        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError("Missing assignment separator")
        key = key.strip()
        if not key:
            raise ValueError("Empty key")
        value = value.lstrip()

        if value.startswith('"'):
            characters = []
            index = 1
            while index < len(value):
                character = value[index]
                if character == '"':
                    trailing = value[index + 1:].lstrip()
                    if trailing and not trailing.startswith("#"):
                        raise ValueError("Invalid content after quoted value")
                    result[key] = "".join(characters)
                    break
                if character == "\\":
                    index += 1
                    if index == len(value):
                        raise ValueError("Unterminated quoted value")
                    character = escapes.get(value[index], value[index])
                characters.append(character)
                index += 1
            else:
                raise ValueError("Unterminated quoted value")
        else:
            for index, character in enumerate(value):
                if character == "#" and (index == 0 or value[index - 1].isspace()):
                    value = value[:index]
                    break
            value = value.rstrip()
            lowered = value.lower()
            if lowered in ("true", "false"):
                result[key] = lowered == "true"
            elif lowered in ("null", "none"):
                result[key] = None
            elif re.fullmatch(r"[+-]?(0|[1-9][0-9]*)", value):
                result[key] = int(value)
            elif re.fullmatch(
                r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)",
                value,
            ):
                result[key] = float(value)
            else:
                result[key] = value

    return result
