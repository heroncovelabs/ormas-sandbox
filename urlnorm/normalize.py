"""RFC 3986 URL path normalization."""

_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    "-._~"
)


def _normalize_percent_encoding(path):
    """Decode escapes for unreserved characters, uppercase the others."""
    out = []
    i = 0
    n = len(path)
    while i < n:
        ch = path[i]
        if ch != "%":
            out.append(ch)
            i += 1
            continue
        hex_digits = path[i + 1:i + 3]
        if len(hex_digits) != 2 or not all(c in _HEX_DIGITS for c in hex_digits):
            raise ValueError(
                "malformed percent-encoding at index %d in %r" % (i, path)
            )
        hex_digits = hex_digits.upper()
        decoded = chr(int(hex_digits, 16))
        if decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hex_digits)
        i += 3
    return "".join(out)


def _remove_last_segment(output):
    """Drop the final segment of the output buffer (RFC 3986 5.2.4)."""
    slash = output.rfind("/")
    if slash == -1:
        return ""
    return output[:slash]


def _remove_dot_segments(path):
    """RFC 3986 section 5.2.4 dot-segment removal."""
    output = ""
    remaining = path
    while remaining:
        if remaining.startswith("../"):
            remaining = remaining[3:]
        elif remaining.startswith("./"):
            remaining = remaining[2:]
        elif remaining.startswith("/./"):
            remaining = "/" + remaining[3:]
        elif remaining == "/.":
            remaining = "/"
        elif remaining.startswith("/../"):
            remaining = "/" + remaining[4:]
            output = _remove_last_segment(output)
        elif remaining == "/..":
            remaining = "/"
            output = _remove_last_segment(output)
        elif remaining == "." or remaining == "..":
            remaining = ""
        else:
            if remaining.startswith("/"):
                next_slash = remaining.find("/", 1)
            else:
                next_slash = remaining.find("/")
            if next_slash == -1:
                output += remaining
                remaining = ""
            else:
                output += remaining[:next_slash]
                remaining = remaining[next_slash:]
    return output


def normalize_path(path):
    """Normalize a URL path per RFC 3986 (see issue.md)."""
    return _remove_dot_segments(_normalize_percent_encoding(path))
