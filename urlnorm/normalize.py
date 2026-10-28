_HEX = "0123456789abcdefABCDEF"
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _normalize_percent(path):
    out = []
    i = 0
    n = len(path)
    while i < n:
        ch = path[i]
        if ch != "%":
            out.append(ch)
            i += 1
            continue
        hh = path[i + 1:i + 3]
        if len(hh) != 2 or hh[0] not in _HEX or hh[1] not in _HEX:
            raise ValueError("malformed percent-encoding at index %d" % i)
        decoded = chr(int(hh, 16))
        if decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hh.upper())
        i += 3
    return "".join(out)


def _remove_dot_segments(path):
    """RFC 3986 section 5.2.4."""
    inp = path
    out = []
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
    """Normalize a URL path per RFC 3986 (see issue.md)."""
    return _remove_dot_segments(_normalize_percent(path))
