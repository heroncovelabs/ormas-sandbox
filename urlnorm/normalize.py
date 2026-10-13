def normalize_path(path):
    """Normalize percent escapes, then remove dot segments per RFC 3986."""
    unreserved = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    hex_digits = "0123456789abcdefABCDEF"
    normalized = []
    index = 0
    while index < len(path):
        if path[index] != "%":
            normalized.append(path[index])
            index += 1
            continue

        escape = path[index + 1:index + 3]
        if len(escape) != 2 or any(char not in hex_digits for char in escape):
            raise ValueError("Malformed percent escape at index {}".format(index))
        char = chr(int(escape, 16))
        normalized.append(char if char in unreserved else "%" + escape.upper())
        index += 3

    # Apply the input/output buffer algorithm from RFC 3986 section 5.2.4.
    path = "".join(normalized)
    output = []
    while path:
        if path.startswith("../"):
            path = path[3:]
        elif path.startswith("./"):
            path = path[2:]
        elif path.startswith("/./") or path == "/.":
            path = "/" + path[3:]
        elif path.startswith("/../") or path == "/..":
            path = "/" + path[4:]
            if output:
                output.pop()
        elif path in (".", ".."):
            path = ""
        else:
            end = path.find("/", 1)
            if end == -1:
                end = len(path)
            output.append(path[:end])
            path = path[end:]

    return "".join(output)
