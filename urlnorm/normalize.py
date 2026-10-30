_HEX_DIGITS = "0123456789ABCDEFabcdef"
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _normalize_percent(path):
    """Apply RFC 3986 section 6.2.2.2 percent-encoding normalization."""
    out = []
    i = 0
    n = len(path)
    while i < n:
        ch = path[i]
        if ch != "%":
            out.append(ch)
            i += 1
            continue
        pair = path[i + 1:i + 3]
        if len(pair) != 2 or any(c not in _HEX_DIGITS for c in pair):
            raise ValueError(f"malformed percent escape at index {i}: {path!r}")
        value = int(pair, 16)
        decoded = chr(value)
        if value < 0x80 and decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + pair.upper())
        i += 3
    return "".join(out)


def _pop_output(out):
    """Remove the last segment and its preceding '/' from the output buffer."""
    idx = out.rfind("/")
    return out[:idx] if idx >= 0 else ""


def _remove_dot_segments(path):
    """Remove dot segments per RFC 3986 section 5.2.4."""
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
            out = _pop_output(out)
        elif inp == "/..":
            inp = "/"
            out = _pop_output(out)
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
    """Normalize a URL path per RFC 3986 (see issue.md)."""
    return _remove_dot_segments(_normalize_percent(path))
