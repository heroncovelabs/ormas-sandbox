"""Parser for the VulcanConf line-based config format."""

import re

_INT_RE = re.compile(r"[+-]?(?:0|[1-9][0-9]*)\Z")
_FLOAT_RE = re.compile(r"[+-]?(?:\d+\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)\Z")
_ESCAPE_MAP = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def parse_config(text):
    """Parse VulcanConf source into a dict. Later keys overwrite earlier ones."""
    result = {}
    for raw_line in text.split("\n"):
        if raw_line.endswith("\r"):
            raw_line = raw_line[:-1]
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if "=" not in raw_line:
            raise ValueError("expected 'key = value': %r" % raw_line)
        key, _, rest = raw_line.partition("=")
        key = key.strip()
        if not key:
            raise ValueError("empty key in line: %r" % raw_line)
        result[key] = _parse_value(rest.lstrip(), raw_line)
    return result


def _parse_value(value, line):
    if value.startswith('"'):
        return _parse_quoted(value, line)
    return _coerce(_strip_inline_comment(value).rstrip())


def _parse_quoted(value, line):
    out = []
    i = 1
    n = len(value)
    while i < n:
        c = value[i]
        if c == "\\":
            if i + 1 < n:
                out.append(_ESCAPE_MAP.get(value[i + 1], value[i + 1]))
                i += 2
            else:
                out.append(c)
                i += 1
            continue
        if c == '"':
            tail = value[i + 1 :].strip()
            if tail and not tail.startswith("#"):
                raise ValueError(
                    "unexpected content after quoted value: %r" % line
                )
            return "".join(out)
        out.append(c)
        i += 1
    raise ValueError("missing closing quote: %r" % line)


def _strip_inline_comment(value):
    for i, c in enumerate(value):
        if c == "#" and (i == 0 or value[i - 1].isspace()):
            return value[:i]
    return value


def _coerce(value):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "none"):
        return None
    if _INT_RE.match(value):
        return int(value)
    if _FLOAT_RE.match(value):
        return float(value)
    return value
