_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def _normalize_percent_encoding(path):
    """Decode unreserved escapes and canonicalize the remaining escapes."""
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
            raise ValueError(f"malformed percent-encoding at index {index}")

        hex_digits = path[index + 1 : index + 3]
        decoded = chr(int(hex_digits, 16))
        if decoded in _UNRESERVED:
            normalized.append(decoded)
        else:
            normalized.append("%" + hex_digits.upper())
        index += 3

    return "".join(normalized)


def _remove_dot_segments(path):
    """Remove dot segments using the algorithm in RFC 3986 section 5.2.4."""
    input_buffer = path
    output = ""

    while input_buffer:
        if input_buffer.startswith("../"):
            input_buffer = input_buffer[3:]
        elif input_buffer.startswith("./"):
            input_buffer = input_buffer[2:]
        elif input_buffer.startswith("/./"):
            input_buffer = input_buffer[2:]
        elif input_buffer == "/.":
            input_buffer = "/"
        elif input_buffer.startswith("/../"):
            input_buffer = input_buffer[3:]
            output = _remove_last_segment(output)
        elif input_buffer == "/..":
            input_buffer = "/"
            output = _remove_last_segment(output)
        elif input_buffer in (".", ".."):
            input_buffer = ""
        else:
            segment_end = input_buffer.find("/", 1)
            if segment_end == -1:
                output += input_buffer
                input_buffer = ""
            else:
                output += input_buffer[:segment_end]
                input_buffer = input_buffer[segment_end:]

    return output


def _remove_last_segment(output):
    separator = output.rfind("/")
    if separator == -1:
        return ""
    return output[:separator]


def normalize_path(path):
    """Return the RFC 3986 normalized form of a URL path string."""
    return _remove_dot_segments(_normalize_percent_encoding(path))
