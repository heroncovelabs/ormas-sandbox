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
    pc = 0
    while pc < len(code):
        instr = code[pc]
        op = instr[0]
        pc += 1
        if op == "PUSH":
            stack.append(instr[1])
        elif op == "LOAD":
            name = instr[1]
            if name not in env:
                raise NameError(f"unbound variable: {name!r}")
            stack.append(env[name])
        elif op in ("ADD", "SUB", "MUL", "DIV"):
            b = stack.pop()
            a = stack.pop()
            if op == "ADD":
                stack.append(a + b)
            elif op == "SUB":
                stack.append(a - b)
            elif op == "MUL":
                stack.append(a * b)
            else:
                stack.append(a / b)
        elif op == "EQ":
            b = stack.pop()
            a = stack.pop()
            stack.append(a == b)
        elif op == "LT":
            b = stack.pop()
            a = stack.pop()
            stack.append(a < b)
        elif op == "GT":
            b = stack.pop()
            a = stack.pop()
            stack.append(a > b)
        elif op == "NOT":
            stack.append(not stack.pop())
        elif op == "DUP":
            stack.append(stack[-1])
        elif op == "POP":
            stack.pop()
        elif op == "JUMP":
            pc = instr[1]
        elif op == "JUMP_IF_FALSE":
            if not stack.pop():
                pc = instr[1]
        else:
            raise ValueError(f"unknown opcode: {op!r}")
    if len(stack) != 1:
        raise RuntimeError(f"expected one value on stack, found {len(stack)}")
    return stack[0]
