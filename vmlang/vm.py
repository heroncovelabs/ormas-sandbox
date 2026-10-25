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
        elif op in {"ADD", "SUB", "MUL", "DIV", "EQ", "LT", "GT"}:
            b = stack.pop()
            a = stack.pop()
            if op == "ADD":
                result = a + b
            elif op == "SUB":
                result = a - b
            elif op == "MUL":
                result = a * b
            elif op == "DIV":
                result = a / b
            elif op == "EQ":
                result = a == b
            elif op == "LT":
                result = a < b
            else:
                result = a > b
            stack.append(result)
        elif op == "NOT":
            stack.append(not stack.pop())
        elif op == "DUP":
            stack.append(stack[-1])
        elif op == "POP":
            stack.pop()
        elif op == "JUMP":
            ip = instruction[1]
        elif op == "JUMP_IF_FALSE":
            if not stack.pop():
                ip = instruction[1]
        else:
            raise ValueError(f"unknown opcode: {op!r}")

    return stack.pop()
