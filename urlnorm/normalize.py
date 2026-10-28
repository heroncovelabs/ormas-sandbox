"""RFC 3986 URL path normalization."""

_HEX_DIGITS = set("0123456789abcdefABCDEF")
_UNRESERVED = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _normalize_percent_encoding(text):
    """Decode unreserved escapes, upper-case the rest, reject malformed."""
    out = []
    i = 0
    length = len(text)
    while i < length:
        char = text[i]
        if char != "%":
            out.append(char)
            i += 1
            continue
        if i + 2 >= length:
            raise ValueError("malformed percent-escape at index %d" % i)
        hi, lo = text[i + 1], text[i + 2]
        if hi not in _HEX_DIGITS or lo not in _HEX_DIGITS:
            raise ValueError("malformed percent-escape at index %d" % i)
        decoded = chr(int(hi + lo, 16))
        if decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hi.upper() + lo.upper())
        i += 3
    return "".join(out)


def _remove_last_segment(output):
    """Drop the last segment (and the slash preceding it) from output."""
    slash = output.rfind("/")
    if slash == -1:
        return ""
    return output[:slash]


def _remove_dot_segments(path):
    """RFC 3986 section 5.2.4 dot-segment removal."""
    input_buffer = path
    output = ""
    while input_buffer:
        if input_buffer.startswith("../"):
            input_buffer = input_buffer[3:]
        elif input_buffer.startswith("./"):
            input_buffer = input_buffer[2:]
        elif input_buffer.startswith("/./"):
            input_buffer = "/" + input_buffer[3:]
        elif input_buffer == "/.":
            input_buffer = "/"
        elif input_buffer.startswith("/../"):
            input_buffer = "/" + input_buffer[4:]
            output = _remove_last_segment(output)
        elif input_buffer == "/..":
            input_buffer = "/"
            output = _remove_last_segment(output)
        elif input_buffer in (".", ".."):
            input_buffer = ""
        else:
            if input_buffer.startswith("/"):
                end = input_buffer.find("/", 1)
            else:
                end = input_buffer.find("/")
            if end == -1:
                output += input_buffer
                input_buffer = ""
            else:
                output += input_buffer[:end]
                input_buffer = input_buffer[end:]
    return output


def normalize_path(path):
    """Normalize a URL path per RFC 3986."""
    if not path:
        return path
    normalized = _normalize_percent_encoding(path)
    return _remove_dot_segments(normalized)
