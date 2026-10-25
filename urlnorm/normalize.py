_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _normalize_percent_encoding(path):
    """Decode unreserved escapes and canonicalize all other escapes."""
    normalized = []
    index = 0

    while index < len(path):
        char = path[index]
        if char != "%":
            normalized.append(char)
            index += 1
            continue

        if (
            index + 2 >= len(path)
            or path[index + 1] not in _HEX_DIGITS
            or path[index + 2] not in _HEX_DIGITS
        ):
            raise ValueError("malformed percent-encoding in URL path")

        decoded = chr(int(path[index + 1 : index + 3], 16))
        if decoded in _UNRESERVED:
            normalized.append(decoded)
        else:
            normalized.append("%" + path[index + 1 : index + 3].upper())
        index += 3

    return "".join(normalized)


def _remove_last_segment(output):
    """Remove the final segment and its preceding slash, if present."""
    return output.rsplit("/", 1)[0] if "/" in output else ""


def _remove_dot_segments(path):
    """Apply the input/output buffer algorithm from RFC 3986 section 5.2.4."""
    output = []

    while path:
        if path.startswith("../"):
            path = path[3:]
        elif path.startswith("./"):
            path = path[2:]
        elif path.startswith("/./"):
            path = path[2:]
        elif path == "/.":
            path = "/"
        elif path.startswith("/../"):
            path = path[3:]
            output = [_remove_last_segment("".join(output))]
        elif path == "/..":
            path = "/"
            output = [_remove_last_segment("".join(output))]
        elif path in (".", ".."):
            path = ""
        else:
            next_slash = path.find("/", 1)
            if next_slash == -1:
                output.append(path)
                path = ""
            else:
                output.append(path[:next_slash])
                path = path[next_slash:]

    return "".join(output)


def normalize_path(path):
    """Normalize percent-encoding, then remove dot segments from a URL path."""
    return _remove_dot_segments(_normalize_percent_encoding(path))
