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
        ip += 1

        if op == "PUSH":
            stack.append(instruction[1])
        elif op == "LOAD":
            name = instruction[1]
            try:
                stack.append(env[name])
            except KeyError:
                raise NameError(f"name {name!r} is not defined") from None
        elif op == "ADD":
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
        elif op == "SUB":
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif op == "MUL":
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
        elif op == "DIV":
            b = stack.pop()
            a = stack.pop()
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
            ip = instruction[1]
        elif op == "JUMP_IF_FALSE":
            value = stack.pop()
            if not value:
                ip = instruction[1]
        else:
            raise ValueError(f"unknown opcode: {op!r}")

    return stack.pop()
