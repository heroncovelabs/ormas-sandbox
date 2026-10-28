"""RFC 3986 URL path normalization."""

_HEXDIGITS = "0123456789abcdefABCDEF"

_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _normalize_percent_encoding(path):
    """Decode percent-escapes of unreserved chars; uppercase the remaining ones."""
    out = []
    i = 0
    n = len(path)
    while i < n:
        ch = path[i]
        if ch != "%":
            out.append(ch)
            i += 1
            continue
        if i + 2 >= n or path[i + 1] not in _HEXDIGITS or path[i + 2] not in _HEXDIGITS:
            raise ValueError("malformed percent-escape in path: %r" % (path,))
        hexdigits = path[i + 1 : i + 3]
        decoded = chr(int(hexdigits, 16))
        if decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hexdigits.upper())
        i += 3
    return "".join(out)


def _remove_dot_segments(path):
    """Apply RFC 3986 section 5.2.4 remove_dot_segments."""
    output = []
    inp = path
    while inp:
        if inp.startswith("../"):
            inp = inp[3:]
        elif inp.startswith("./"):
            inp = inp[2:]
        elif inp.startswith("/./"):
            inp = "/" + inp[3:]
        elif inp == "/.":
            inp = "/"
        elif inp.startswith("/../"):
            inp = "/" + inp[4:]
            if output:
                output.pop()
        elif inp == "/..":
            inp = "/"
            if output:
                output.pop()
        elif inp in (".", ".."):
            inp = ""
        else:
            start = 1 if inp.startswith("/") else 0
            idx = inp.find("/", start)
            if idx == -1:
                output.append(inp)
                inp = ""
            else:
                output.append(inp[:idx])
                inp = inp[idx:]
    return "".join(output)


def normalize_path(path):
    """Normalize a URL path per RFC 3986."""
    return _remove_dot_segments(_normalize_percent_encoding(path))
