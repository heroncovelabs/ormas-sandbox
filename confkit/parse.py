import re


_INTEGER = re.compile(r"[+-]?(0|[1-9][0-9]*)")
_FLOAT = re.compile(
    r"[+-]?(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)"
)
_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def parse_config(text):
    """Parse line-based VulcanConf source, with later keys taking precedence."""
    config = {}
    for line_number, line in enumerate(text.split("\n"), 1):
        line = line.removesuffix("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Missing '=' on line {line_number}")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Empty key on line {line_number}")
        value = value.lstrip()

        if value.startswith('"'):
            characters = []
            index = 1
            while index < len(value):
                character = value[index]
                if character == '"':
                    trailing = value[index + 1:].lstrip()
                    if trailing and not trailing.startswith("#"):
                        raise ValueError(f"Trailing content on line {line_number}")
                    break
                if character == "\\":
                    index += 1
                    if index == len(value):
                        raise ValueError(f"Unclosed quoted value on line {line_number}")
                    character = _ESCAPES.get(value[index], value[index])
                characters.append(character)
                index += 1
            else:
                raise ValueError(f"Unclosed quoted value on line {line_number}")
            config[key] = "".join(characters)
            continue

        for index, character in enumerate(value):
            if character == "#" and (index == 0 or value[index - 1].isspace()):
                value = value[:index]
                break
        value = value.rstrip()
        lowered = value.lower()
        if lowered in ("true", "false"):
            parsed = lowered == "true"
        elif lowered in ("null", "none"):
            parsed = None
        elif _INTEGER.fullmatch(value):
            parsed = int(value)
        elif _FLOAT.fullmatch(value):
            parsed = float(value)
        else:
            parsed = value
        config[key] = parsed
    return config
