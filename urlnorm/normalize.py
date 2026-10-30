import re

_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_HEX = "0123456789abcdefABCDEF"


def _normalize_percent(path):
    out = []
    i = 0
    n = len(path)
    while i < n:
        c = path[i]
        if c != "%":
            out.append(c)
            i += 1
            continue
        hh = path[i + 1:i + 3]
        if len(hh) != 2 or hh[0] not in _HEX or hh[1] not in _HEX:
            raise ValueError("malformed percent-encoding at index %d" % i)
        ch = chr(int(hh, 16))
        out.append(ch if ch in _UNRESERVED else "%" + hh.upper())
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
            m = re.match(r"/?[^/]*", inp)
            seg = m.group(0)
            out.append(seg)
            inp = inp[len(seg):]
    return "".join(out)


def normalize_path(path):
    """Normalize a URL path per RFC 3986 (see issue.md)."""
    return _remove_dot_segments(_normalize_percent(path))
