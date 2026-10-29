_HEXDIGITS = frozenset("0123456789abcdefABCDEF")
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _normalize_percent_encoding(path):
    """Decode unreserved escapes and upper-case the rest.

    Raises ValueError on a '%' not followed by two hex digits.
    """
    out = []
    i = 0
    n = len(path)
    while i < n:
        ch = path[i]
        if ch != "%":
            out.append(ch)
            i += 1
            continue
        if i + 2 >= n:
            raise ValueError(f"malformed percent escape at index {i}")
        h1, h2 = path[i + 1], path[i + 2]
        if h1 not in _HEXDIGITS or h2 not in _HEXDIGITS:
            raise ValueError(f"malformed percent escape at index {i}")
        value = int(h1 + h2, 16)
        decoded = chr(value)
        if value < 0x80 and decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + (h1 + h2).upper())
        i += 3
    return "".join(out)


def _remove_dot_segments(path):
    """Remove dot segments per RFC 3986 section 5.2.4."""
    inp = path
    out = []  # output segments, each including its leading "/" if any
    while inp:
        if inp.startswith("../"):
            inp = inp[3:]
        elif inp.startswith("./"):
            inp = inp[2:]
        elif inp.startswith("/./"):
            inp = inp[2:]
        elif inp == "/.":
            inp = "/"
        elif inp.startswith("/../"):
            inp = inp[3:]
            if out:
                out.pop()
        elif inp == "/..":
            inp = "/"
            if out:
                out.pop()
        elif inp in (".", ".."):
            inp = ""
        else:
            start = 1 if inp.startswith("/") else 0
            end = inp.find("/", start)
            if end == -1:
                end = len(inp)
            out.append(inp[:end])
            inp = inp[end:]
    return "".join(out)


def normalize_path(path):
    """Normalize a URL path per RFC 3986 (see issue.md).

    Percent-encoding normalization runs first, then dot-segment removal.
    Raises ValueError on malformed percent escapes.
    """
    return _remove_dot_segments(_normalize_percent_encoding(path))
