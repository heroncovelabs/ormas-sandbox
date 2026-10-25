"""Lower an expression AST to a flat list of stack-machine instructions.

The instruction set (shared contract with ``vmlang/vm.py``) is documented in the
issue. Each instruction is a tuple ``(OPCODE, *operands)`` where ``OPCODE`` is one
of the uppercase names in that table. Jump operands are absolute indices into the
returned list. Short-circuit ``and``/``or`` and ``if`` require forward jumps whose
targets are only known once the skipped code has been emitted (backpatching).
"""


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    code = []
    binary_ops = {
        "+": "ADD",
        "-": "SUB",
        "*": "MUL",
        "/": "DIV",
        "==": "EQ",
        "<": "LT",
        ">": "GT",
    }

    def patch(index, target):
        opcode = code[index][0]
        code[index] = (opcode, target)

    def emit(node):
        op = node[0]
        if op == "lit":
            code.append(("PUSH", node[1]))
        elif op == "var":
            code.append(("LOAD", node[1]))
        elif op == "not":
            emit(node[1])
            code.append(("NOT",))
        elif op in binary_ops:
            emit(node[1])
            emit(node[2])
            code.append((binary_ops[op],))
        elif op == "and":
            emit(node[1])
            code.append(("DUP",))
            skip_right = len(code)
            code.append(("JUMP_IF_FALSE", None))
            code.append(("POP",))
            emit(node[2])
            patch(skip_right, len(code))
        elif op == "or":
            emit(node[1])
            code.append(("DUP",))
            evaluate_right = len(code)
            code.append(("JUMP_IF_FALSE", None))
            skip_right = len(code)
            code.append(("JUMP", None))
            patch(evaluate_right, len(code))
            code.append(("POP",))
            emit(node[2])
            patch(skip_right, len(code))
        elif op == "if":
            emit(node[1])
            jump_to_else = len(code)
            code.append(("JUMP_IF_FALSE", None))
            emit(node[2])
            jump_to_end = len(code)
            code.append(("JUMP", None))
            patch(jump_to_else, len(code))
            emit(node[3])
            patch(jump_to_end, len(code))
        else:
            raise ValueError(f"unknown AST node: {op!r}")

    emit(ast)
    return code
