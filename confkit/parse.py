import re


def parse_config(text):
    """Parse the VulcanConf config format into a dict (see issue.md)."""
    result = {}
    for line in text.split("\n"):
        if line.endswith("\r"):
            line = line[:-1]
        if not line.strip() or line.lstrip().startswith("#"):
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
            escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
            index = 1
            while index < len(value):
                char = value[index]
                if char == '"':
                    remainder = value[index + 1:].lstrip()
                    if remainder and not remainder.startswith("#"):
                        raise ValueError("Unexpected content after quoted value")
                    value = "".join(characters)
                    break
                if char == "\\":
                    index += 1
                    if index == len(value):
                        raise ValueError("Unterminated quoted value")
                    char = escapes.get(value[index], value[index])
                characters.append(char)
                index += 1
            else:
                raise ValueError("Unterminated quoted value")
        else:
            for index, char in enumerate(value):
                if char == "#" and (index == 0 or value[index - 1].isspace()):
                    value = value[:index]
                    break
            value = value.rstrip()
            if value:
                lowered = value.lower()
                if lowered in ("true", "false"):
                    value = lowered == "true"
                elif lowered in ("null", "none"):
                    value = None
                elif re.fullmatch(r"[+-]?(0|[1-9][0-9]*)", value):
                    value = int(value)
                elif re.fullmatch(
                    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)",
                    value,
                ):
                    value = float(value)

        result[key] = value

    return result
