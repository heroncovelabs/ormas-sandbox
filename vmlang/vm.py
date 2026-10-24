"""A stack machine that executes the instruction list produced by the compiler.

It must implement exactly the instruction set documented in the issue, treating
jump operands as absolute indices into the code list. A well-formed program
leaves exactly one value on the stack; ``run`` returns it.
"""


import operator

_BINARY = {
    "ADD": operator.add,
    "SUB": operator.sub,
    "MUL": operator.mul,
    "DIV": operator.truediv,
    "EQ": operator.eq,
    "LT": operator.lt,
    "GT": operator.gt,
}


def run(code, env=None):
    """Execute ``code`` against variable bindings ``env``; return the result."""
    if env is None:
        env = {}
    stack = []
    ip = 0
    while ip < len(code):
        instr = code[ip]
        op = instr[0]
        ip += 1
        if op == "PUSH":
            stack.append(instr[1])
        elif op == "LOAD":
            name = instr[1]
            if name not in env:
                raise NameError(f"name {name!r} is not defined")
            stack.append(env[name])
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
            ip = instr[1]
        elif op == "JUMP_IF_FALSE":
            if not stack.pop():
                ip = instr[1]
        else:
            raise ValueError(f"unknown opcode {op!r}")
    if len(stack) != 1:
        raise RuntimeError(f"malformed program: stack has {len(stack)} values at exit")
    return stack[0]
