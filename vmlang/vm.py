"""A stack machine that executes the instruction list produced by the compiler.

It must implement exactly the instruction set documented in the issue, treating
jump operands as absolute indices into the code list. A well-formed program
leaves exactly one value on the stack; ``run`` returns it.
"""

_BINARY = {
    "ADD": lambda a, b: a + b,
    "SUB": lambda a, b: a - b,
    "MUL": lambda a, b: a * b,
    "DIV": lambda a, b: a / b,
    "EQ": lambda a, b: a == b,
    "LT": lambda a, b: a < b,
    "GT": lambda a, b: a > b,
}


def run(code, env=None):
    """Execute ``code`` against variable bindings ``env``; return the result."""
    if env is None:
        env = {}

    stack = []
    ip = 0
    n = len(code)

    while ip < n:
        inst = code[ip]
        op = inst[0]
        ip += 1

        if op == "PUSH":
            stack.append(inst[1])
        elif op == "LOAD":
            name = inst[1]
            try:
                stack.append(env[name])
            except KeyError:
                raise NameError(f"name {name!r} is not defined") from None
        elif op in _BINARY:
            b = stack.pop()
            a = stack.pop()
            stack.append(_BINARY[op](a, b))
        elif op == "NOT":
            stack.append(not stack.pop())
        elif op == "DUP":
            stack.append(stack[-1])
        elif op == "POP":
            stack.pop()
        elif op == "JUMP":
            ip = inst[1]
        elif op == "JUMP_IF_FALSE":
            if not stack.pop():
                ip = inst[1]
        else:
            raise ValueError(f"unknown opcode: {op!r}")

    return stack[-1]
