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
    end = len(code)
    while 0 <= ip < end:
        instr = code[ip]
        op = instr[0]
        if op == "PUSH":
            stack.append(instr[1])
            ip += 1
        elif op == "LOAD":
            try:
                stack.append(env[instr[1]])
            except KeyError:
                raise NameError(f"unbound variable {instr[1]!r}") from None
            ip += 1
        elif op == "ADD":
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
            ip += 1
        elif op == "SUB":
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
            ip += 1
        elif op == "MUL":
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
            ip += 1
        elif op == "DIV":
            b = stack.pop()
            a = stack.pop()
            stack.append(a / b)
            ip += 1
        elif op == "EQ":
            b = stack.pop()
            a = stack.pop()
            stack.append(a == b)
            ip += 1
        elif op == "LT":
            b = stack.pop()
            a = stack.pop()
            stack.append(a < b)
            ip += 1
        elif op == "GT":
            b = stack.pop()
            a = stack.pop()
            stack.append(a > b)
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
            value = stack.pop()
            ip = instr[1] if not value else ip + 1
        else:
            raise ValueError(f"unknown opcode {op!r} at index {ip}")
    if not stack:
        raise ValueError("program finished with an empty stack")
    return stack[-1]
