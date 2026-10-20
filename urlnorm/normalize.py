import re

_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_HEX2 = re.compile(r"[0-9A-Fa-f]{2}")


def _normalize_percent(path):
    """Step 1: decode unreserved escapes, uppercase the rest, reject malformed."""
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
        if len(hex_digits) != 2 or not _HEX2.fullmatch(hex_digits):
            raise ValueError("malformed percent-encoding at index %d" % i)
        decoded = chr(int(hex_digits, 16))
        if decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hex_digits.upper())
        i += 3
    return "".join(out)


def _remove_dot_segments(path):
    """Step 2: RFC 3986 section 5.2.4 remove_dot_segments."""
    source = path
    output = []
    while source:
        if source.startswith("../"):
            source = source[3:]
        elif source.startswith("./"):
            source = source[2:]
        elif source.startswith("/./"):
            source = source[2:]
        elif source == "/.":
            source = "/"
        elif source.startswith("/../"):
            source = source[3:]
            if output:
                output.pop()
        elif source == "/..":
            source = "/"
            if output:
                output.pop()
        elif source in (".", ".."):
            source = ""
        else:
            start = 1 if source.startswith("/") else 0
            end = source.find("/", start)
            if end == -1:
                end = len(source)
            output.append(source[:end])
            source = source[end:]
    return "".join(output)


def normalize_path(path):
    """Normalize a URL path per RFC 3986 (see issue.md)."""
    return _remove_dot_segments(_normalize_percent(path))
