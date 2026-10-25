_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_HEXDIGITS = frozenset("0123456789abcdefABCDEF")


def _normalize_percent(path):
    """Decode unreserved percent-escapes and upper-case the rest (RFC 3986 6.2.2.2)."""
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
        if (
            len(hex_pair) != 2
            or hex_pair[0] not in _HEXDIGITS
            or hex_pair[1] not in _HEXDIGITS
        ):
            raise ValueError("malformed percent-encoding at index %d" % i)
        value = int(hex_pair, 16)
        decoded = chr(value)
        if value < 0x80 and decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hex_pair.upper())
        i += 3
    return "".join(out)


def _remove_dot_segments(path):
    """Remove dot segments per RFC 3986 section 5.2.4."""
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
            # Move the first path segment (including its leading "/" if any) to output.
            start = 1 if inp.startswith("/") else 0
            end = inp.find("/", start)
            if end == -1:
                end = len(inp)
            output.append(inp[:end])
            inp = inp[end:]
    return "".join(output)


def normalize_path(path):
    """Normalize percent-encoding, then remove RFC 3986 dot segments.

    Decode unreserved escapes and uppercase all other escapes. Malformed
    percent-encoding raises ValueError, including in segments removed later.
    """
    return _remove_dot_segments(_normalize_percent(path))
