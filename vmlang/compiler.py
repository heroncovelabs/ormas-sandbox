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
        "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
        "==": "EQ", "<": "LT", ">": "GT",
    }

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
        elif op == "if":
            emit(node[1])
            false_jump = len(code)
            code.append(("JUMP_IF_FALSE", None))
            emit(node[2])
            end_jump = len(code)
            code.append(("JUMP", None))
            code[false_jump] = ("JUMP_IF_FALSE", len(code))
            emit(node[3])
            code[end_jump] = ("JUMP", len(code))
        elif op == "and":
            emit(node[1])
            code.append(("DUP",))
            end_jump = len(code)
            code.append(("JUMP_IF_FALSE", None))
            code.append(("POP",))
            emit(node[2])
            code[end_jump] = ("JUMP_IF_FALSE", len(code))
        elif op == "or":
            emit(node[1])
            code.append(("DUP",))
            false_jump = len(code)
            code.append(("JUMP_IF_FALSE", None))
            end_jump = len(code)
            code.append(("JUMP", None))
            code[false_jump] = ("JUMP_IF_FALSE", len(code))
            code.append(("POP",))
            emit(node[2])
            code[end_jump] = ("JUMP", len(code))
        else:
            raise ValueError(f"Unknown expression operator: {op!r}")

    emit(ast)
    return code
