_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _normalize_percent_encoding(path):
    """Decode unreserved escapes and uppercase the rest, in one left-to-right pass."""
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
        hi, lo = path[i + 1], path[i + 2]
        if hi not in _HEX_DIGITS or lo not in _HEX_DIGITS:
            raise ValueError(f"malformed percent escape at index {i}")
        char = chr(int(hi + lo, 16))
        if char in _UNRESERVED:
            out.append(char)
        else:
            out.append("%" + hi.upper() + lo.upper())
        i += 3
    return "".join(out)


def _remove_last_segment(out):
    idx = out.rfind("/")
    return out[:idx] if idx >= 0 else ""


def _remove_dot_segments(path):
    """RFC 3986 section 5.2.4 remove_dot_segments."""
    inp = path
    out = ""
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
            out = _remove_last_segment(out)
        elif inp == "/..":
            inp = "/"
            out = _remove_last_segment(out)
        elif inp in (".", ".."):
            inp = ""
        else:
            start = 1 if inp.startswith("/") else 0
            end = inp.find("/", start)
            if end == -1:
                end = len(inp)
            out += inp[:end]
            inp = inp[end:]
    return out


def normalize_path(path):
    """Normalize percent escapes, then remove RFC 3986 dot segments.

    Decode escapes for unreserved characters and uppercase all other escapes.
    Encoded dots participate in dot-segment removal after decoding.
    Malformed percent escapes raise ValueError.
    """
    return _remove_dot_segments(_normalize_percent_encoding(path))
