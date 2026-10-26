"""RFC 3986 URL path normalization.

`normalize_path` applies, in order:

1. percent-encoding normalization (decode unreserved octets, upper-case the
   hex digits of every other escape, reject malformed escapes), then
2. dot-segment removal per RFC 3986 section 5.2.4.
"""

_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    "-._~"
)

_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def _normalize_percent(path):
    """Step 1: decode unreserved %HH escapes, upper-case the rest."""
    out = []
    i = 0
    n = len(path)
    while i < n:
        char = path[i]
        if char != "%":
            out.append(char)
            i += 1
            continue
        if (
            i + 2 >= n
            or path[i + 1] not in _HEX_DIGITS
            or path[i + 2] not in _HEX_DIGITS
        ):
            raise ValueError("malformed percent-escape in path: %r" % (path,))
        hh = path[i + 1 : i + 3]
        decoded = chr(int(hh, 16))
        if decoded in _UNRESERVED:
            out.append(decoded)
        else:
            out.append("%" + hh.upper())
        i += 3
    return "".join(out)


def _remove_dot_segments(path):
    """Step 2: RFC 3986 section 5.2.4 remove_dot_segments."""
    output = []
    buffer = path
    while buffer:
        if buffer.startswith("../") or buffer.startswith("./"):
            buffer = buffer.partition("/")[2]
        if buffer.startswith("/./"):
            buffer = "/" + buffer[3:]
        elif buffer == "/.":
            buffer = "/"
        elif buffer.startswith("/../"):
            buffer = "/" + buffer[4:]
            if output:
                output.pop()
        elif buffer == "/..":
            buffer = "/"
            if output:
                output.pop()
        elif buffer == "." or buffer == "..":
            buffer = ""
        else:
            slash = buffer.find("/", 1) if buffer.startswith("/") else buffer.find("/")
            if slash == -1:
                output.append(buffer)
                buffer = ""
            else:
                output.append(buffer[:slash])
                buffer = buffer[slash:]
    return "".join(output)


def normalize_path(path):
    """Return the normalized form of a URL path string.

    Percent-encoding is normalized first, so an encoded dot (e.g. %2E)
    participates in dot-segment removal.  A '%' not followed by two hex
    digits is malformed and raises ValueError.
    """
    return _remove_dot_segments(_normalize_percent(path))
