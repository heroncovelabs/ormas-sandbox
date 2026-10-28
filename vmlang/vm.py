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
    size = len(code)

    while ip < size:
        instr = code[ip]
        opcode = instr[0]
        ip += 1

        if opcode == "PUSH":
            stack.append(instr[1])
        elif opcode == "LOAD":
            name = instr[1]
            if name not in env:
                raise NameError("name %r is not defined" % (name,))
            stack.append(env[name])
        elif opcode == "ADD":
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
        elif opcode == "SUB":
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif opcode == "MUL":
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
        elif opcode == "DIV":
            b = stack.pop()
            a = stack.pop()
            stack.append(a / b)
        elif opcode == "EQ":
            b = stack.pop()
            a = stack.pop()
            stack.append(a == b)
        elif opcode == "LT":
            b = stack.pop()
            a = stack.pop()
            stack.append(a < b)
        elif opcode == "GT":
            b = stack.pop()
            a = stack.pop()
            stack.append(a > b)
        elif opcode == "NOT":
            stack.append(not stack.pop())
        elif opcode == "DUP":
            stack.append(stack[-1])
        elif opcode == "POP":
            stack.pop()
        elif opcode == "JUMP":
            ip = instr[1]
        elif opcode == "JUMP_IF_FALSE":
            if not stack.pop():
                ip = instr[1]
        else:
            raise ValueError("unknown opcode: %r" % (opcode,))

    if len(stack) != 1:
        raise ValueError("program left %d values on the stack" % (len(stack),))
    return stack[0]
