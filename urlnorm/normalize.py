_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_HEX = frozenset("0123456789abcdefABCDEF")


def _normalize_percent(path):
    """Decode %HH escapes of unreserved characters; uppercase the rest."""
    out = []
    i = 0
    n = len(path)
    while i < n:
        c = path[i]
        if c != "%":
            out.append(c)
            i += 1
            continue
        pair = path[i + 1:i + 3]
        if len(pair) != 2 or pair[0] not in _HEX or pair[1] not in _HEX:
            raise ValueError("malformed percent-encoding in %r" % path)
        decoded = chr(int(pair, 16))
        if decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + pair.upper())
        i += 3
    return "".join(out)


def _remove_dot_segments(path):
    """RFC 3986 section 5.2.4."""
    data = path
    output = []
    while data:
        if data.startswith("../"):
            data = data[3:]
        elif data.startswith("./"):
            data = data[2:]
        elif data.startswith("/./"):
            data = data[2:]
        elif data == "/.":
            data = "/"
        elif data.startswith("/../"):
            data = data[3:]
            if output:
                output.pop()
        elif data == "/..":
            data = "/"
            if output:
                output.pop()
        elif data in (".", ".."):
            data = ""
        else:
            start = 1 if data.startswith("/") else 0
            end = data.find("/", start)
            if end == -1:
                end = len(data)
            output.append(data[:end])
            data = data[end:]
    return "".join(output)


def normalize_path(path):
    """Normalize a URL path per RFC 3986 (see issue.md)."""
    return _remove_dot_segments(_normalize_percent(path))
