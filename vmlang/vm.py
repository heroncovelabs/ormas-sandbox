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
        instr = code[ip]
        op = instr[0]
        if op == "PUSH":
            stack.append(instr[1])
            ip += 1
        elif op == "LOAD":
            name = instr[1]
            if name not in env:
                raise NameError(f"unbound variable: {name!r}")
            stack.append(env[name])
            ip += 1
        elif op in _BINARY:
            b = stack.pop()
            a = stack.pop()
            stack.append(_BINARY[op](a, b))
            ip += 1
        elif op == "NOT":
            stack.append(not stack.pop())
            ip += 1
        elif op == "DUP":
            stack.append(stack[-1])
            ip += 1
        elif op == "POP":
            stack.pop()
            ip += 1
        elif op == "JUMP":
            ip = instr[1]
        elif op == "JUMP_IF_FALSE":
            cond = stack.pop()
            ip = instr[1] if not cond else ip + 1
        else:
            raise ValueError(f"unknown opcode: {op!r}")
    if len(stack) != 1:
        raise RuntimeError(f"expected exactly one result on stack, found {len(stack)}")
    return stack[0]
