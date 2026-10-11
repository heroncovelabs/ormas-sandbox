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
        op = instruction[0]
        if op == "PUSH":
            stack.append(instruction[1])
        elif op == "LOAD":
            name = instruction[1]
            try:
                value = env[name]
            except KeyError:
                raise NameError(f"name {name!r} is not defined") from None
            stack.append(value)
        elif op in ("ADD", "SUB", "MUL", "DIV", "EQ", "LT", "GT"):
            b = stack.pop()
            a = stack.pop()
            if op == "ADD":
                value = a + b
            elif op == "SUB":
                value = a - b
            elif op == "MUL":
                value = a * b
            elif op == "DIV":
                value = a / b
            elif op == "EQ":
                value = a == b
            elif op == "LT":
                value = a < b
            else:
                value = a > b
            stack.append(value)
        elif op == "NOT":
            stack.append(not stack.pop())
        elif op == "DUP":
            stack.append(stack[-1])
        elif op == "POP":
            stack.pop()
        elif op == "JUMP":
            ip = instruction[1]
            continue
        elif op == "JUMP_IF_FALSE":
            if not stack.pop():
                ip = instruction[1]
                continue
        else:
            raise ValueError(f"Unknown opcode: {op!r}")
        ip += 1
    return stack.pop()
