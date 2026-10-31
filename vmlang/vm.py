"""A stack machine that executes the instruction list produced by the compiler.

It must implement exactly the instruction set documented in the issue, treating
jump operands as absolute indices into the code list. A well-formed program
leaves exactly one value on the stack; ``run`` returns it.
"""

_BINOPS = {
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
    env = {} if env is None else env
    stack = []
    ip = 0
    while ip < len(code):
        op, *args = code[ip]
        ip += 1
        if op == "PUSH":
            stack.append(args[0])
        elif op == "LOAD":
            name = args[0]
            if name not in env:
                raise NameError(f"name {name!r} is not defined")
            stack.append(env[name])
        elif op in _BINOPS:
            b = stack.pop()
            a = stack.pop()
            stack.append(_BINOPS[op](a, b))
        elif op == "NOT":
            stack.append(not stack.pop())
        elif op == "DUP":
            stack.append(stack[-1])
        elif op == "POP":
            stack.pop()
        elif op == "JUMP":
            ip = args[0]
        elif op == "JUMP_IF_FALSE":
            if not stack.pop():
                ip = args[0]
        else:
            raise ValueError(f"unknown opcode: {op!r}")
    if len(stack) != 1:
        raise RuntimeError(f"program left {len(stack)} values on the stack")
    return stack[0]
