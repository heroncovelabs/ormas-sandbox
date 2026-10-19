"""A stack machine that executes the instruction list produced by the compiler.

It must implement exactly the instruction set documented in the issue, treating
jump operands as absolute indices into the code list. A well-formed program
leaves exactly one value on the stack; ``run`` returns it.
"""


def run(code, env=None):
    """Execute ``code`` against variable bindings ``env``; return the result."""
    if env is None:
        env = {}
    stack = []
    ip = 0

    while ip < len(code):
        instruction = code[ip]
        opcode = instruction[0]

        if opcode == "PUSH":
            stack.append(instruction[1])
        elif opcode == "LOAD":
            name = instruction[1]
            try:
                value = env[name]
            except KeyError:
                raise NameError(f"name {name!r} is not defined") from None
            stack.append(value)
        elif opcode in ("ADD", "SUB", "MUL", "DIV", "EQ", "LT", "GT"):
            b = stack.pop()
            a = stack.pop()
            if opcode == "ADD":
                result = a + b
            elif opcode == "SUB":
                result = a - b
            elif opcode == "MUL":
                result = a * b
            elif opcode == "DIV":
                result = a / b
            elif opcode == "EQ":
                result = a == b
            elif opcode == "LT":
                result = a < b
            else:
                result = a > b
            stack.append(result)
        elif opcode == "NOT":
            stack.append(not stack.pop())
        elif opcode == "DUP":
            stack.append(stack[-1])
        elif opcode == "POP":
            stack.pop()
        elif opcode == "JUMP":
            ip = instruction[1]
            continue
        elif opcode == "JUMP_IF_FALSE":
            if not stack.pop():
                ip = instruction[1]
                continue
        else:
            raise ValueError(f"Unknown opcode: {opcode!r}")

        ip += 1

    return stack.pop()
