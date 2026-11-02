def normalize_path(path):
    """Normalize percent-encoding and remove dot segments per RFC 3986."""
    hex_digits = "0123456789abcdefABCDEF"
    unreserved = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    )
    normalized = []
    index = 0

    while index < len(path):
        if path[index] != "%":
            normalized.append(path[index])
            index += 1
            continue

        escape = path[index + 1:index + 3]
        if len(escape) != 2 or any(char not in hex_digits for char in escape):
            raise ValueError("Malformed percent escape in URL path")

        decoded = chr(int(escape, 16))
        if decoded in unreserved:
            normalized.append(decoded)
        else:
            normalized.append("%" + escape.upper())
        index += 3

    # Validate all escapes before removing segments, including those in
    # segments that will be removed.
    path = "".join(normalized)
    output = []
    index = 0
    length = len(path)

    while index < length:
        if path.startswith("../", index):
            index += 3
        elif path.startswith("./", index):
            index += 2
        elif path.startswith("/./", index):
            # Leave the final slash as the replacement for /./.
            index += 2
        elif path.startswith("/.", index) and index + 2 == length:
            output.append("/")
            break
        elif path.startswith("/../", index):
            # Leave the final slash as the replacement for /../.
            index += 3
            if output:
                output.pop()
        elif path.startswith("/..", index) and index + 3 == length:
            if output:
                output.pop()
            output.append("/")
            break
        elif length - index <= 2 and path[index:] in (".", ".."):
            break
        else:
            # Each output chunk is one segment and its preceding slash, if any.
            # Empty segments are represented by a slash of their own.
            start = index + 1 if path[index] == "/" else index
            end = path.find("/", start)
            if end == -1:
                end = length
            output.append(path[index:end])
            index = end

    return "".join(output)
