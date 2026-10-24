_HEXDIGITS = "0123456789ABCDEFabcdef"
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _normalize_percent(path):
    """Step 1: percent-encoding normalization (single left-to-right pass)."""
    out = []
    i = 0
    n = len(path)
    while i < n:
        ch = path[i]
        if ch != "%":
            out.append(ch)
            i += 1
            continue
        hex_pair = path[i + 1:i + 3]
        if len(hex_pair) != 2 or any(c not in _HEXDIGITS for c in hex_pair):
            raise ValueError(f"malformed percent escape at index {i}: {path[i:i + 3]!r}")
        value = int(hex_pair, 16)
        decoded = chr(value)
        if value < 0x80 and decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hex_pair.upper())
        i += 3
    return "".join(out)


def _remove_last_segment(output):
    idx = output.rfind("/")
    return output[:idx] if idx >= 0 else ""


def _remove_dot_segments(path):
    """Step 2: RFC 3986 section 5.2.4 remove_dot_segments."""
    data = path
    output = ""
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
            output = _remove_last_segment(output)
        elif data == "/..":
            data = "/"
            output = _remove_last_segment(output)
        elif data in (".", ".."):
            data = ""
        else:
            start = 1 if data.startswith("/") else 0
            idx = data.find("/", start)
            end = idx if idx >= 0 else len(data)
            output += data[:end]
            data = data[end:]
    return output


def normalize_path(path):
    """Normalize percent escapes, then remove RFC 3986 dot segments.

    Decode unreserved characters and uppercase all other percent escapes.
    Raise ValueError for malformed percent escapes. An empty path stays empty.
    """
    return _remove_dot_segments(_normalize_percent(path))
