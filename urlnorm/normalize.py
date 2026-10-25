_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_HEX = frozenset("0123456789abcdefABCDEF")


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
        hex_digits = path[i + 1:i + 3]
        if len(hex_digits) != 2 or not all(c in _HEX for c in hex_digits):
            raise ValueError("malformed percent-encoding at index %d" % i)
        decoded = chr(int(hex_digits, 16))
        if decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hex_digits.upper())
        i += 3
    return "".join(out)


def _remove_dot_segments(path):
    # RFC 3986 section 5.2.4 algorithm.
    inp = path
    output = []
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
                idx = len(inp)
            output.append(inp[:idx])
            inp = inp[idx:]
    return "".join(output)


def normalize_path(path):
    """Normalize a URL path per RFC 3986 (see issue.md)."""
    return _remove_dot_segments(_normalize_percent(path))
