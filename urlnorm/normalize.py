def normalize_path(path):
    """Normalize percent escapes, then remove RFC 3986 dot segments."""
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
        decoded = chr(int(escape, 16))
        normalized.append(decoded if decoded in unreserved else "%" + escape.upper())
        index += 3

    # Each output entry is one segment, including its leading slash, if any.
    # Keeping empty segments preserves repeated slashes and trailing slashes.
    path = "".join(normalized)
    output = []
    index = 0
    while index < len(path):
        remaining = len(path) - index
        if path.startswith("../", index):
            index += 3
        elif path.startswith("./", index):
            index += 2
        elif path.startswith("/./", index):
            index += 2
        elif remaining == 2 and path.startswith("/.", index):
            output.append("/")
            break
        elif path.startswith("/../", index):
            index += 3
            if output:
                output.pop()
        elif remaining == 3 and path.startswith("/..", index):
            if output:
                output.pop()
            output.append("/")
            break
        elif remaining <= 2 and path[index:] in (".", ".."):
            break
        else:
            end = path.find("/", index + 1 if path[index] == "/" else index)
            if end == -1:
                end = len(path)
            output.append(path[index:end])
            index = end
    return "".join(output)
