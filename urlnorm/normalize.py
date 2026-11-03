import string

_HEX = set(string.hexdigits)
_UNRESERVED = set(string.ascii_letters + string.digits + "-._~")


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
        if len(hh) != 2 or not all(c in _HEX for c in hh):
            raise ValueError("malformed percent-encoding at index %d" % i)
        decoded = chr(int(hh, 16))
        out.append(decoded if decoded in _UNRESERVED else "%" + hh.upper())
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
