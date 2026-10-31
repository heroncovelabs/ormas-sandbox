"""Lower an expression AST to a flat list of stack-machine instructions.

The instruction set (shared contract with ``vmlang/vm.py``) is documented in the
issue. Each instruction is a tuple ``(OPCODE, *operands)`` where ``OPCODE`` is one
of the uppercase names in that table. Jump operands are absolute indices into the
returned list. Short-circuit ``and``/``or`` and ``if`` require forward jumps whose
targets are only known once the skipped code has been emitted (backpatching).
"""


_BINARY_OPCODES = {
    "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
    "==": "EQ", "<": "LT", ">": "GT",
}


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    code = []

    def emit(node):
        op = node[0]
        if op == "lit":
            code.append(("PUSH", node[1]))
        elif op == "var":
            code.append(("LOAD", node[1]))
        elif op == "not":
            emit(node[1])
            code.append(("NOT",))
        elif op in _BINARY_OPCODES:
            emit(node[1])
            emit(node[2])
            code.append((_BINARY_OPCODES[op],))
        elif op == "if":
            emit(node[1])
            branch = len(code)
            code.append(("JUMP_IF_FALSE", None))
            emit(node[2])
            end = len(code)
            code.append(("JUMP", None))
            code[branch] = ("JUMP_IF_FALSE", len(code))
            emit(node[3])
            code[end] = ("JUMP", len(code))
        elif op == "and":
            emit(node[1])
            # The conditional consumes the copy, preserving the operand value.
            code.append(("DUP",))
            end = len(code)
            code.append(("JUMP_IF_FALSE", None))
            code.append(("POP",))
            emit(node[2])
            code[end] = ("JUMP_IF_FALSE", len(code))
        elif op == "or":
            emit(node[1])
            code.append(("DUP",))
            branch = len(code)
            code.append(("JUMP_IF_FALSE", None))
            end = len(code)
            code.append(("JUMP", None))
            code[branch] = ("JUMP_IF_FALSE", len(code))
            code.append(("POP",))
            emit(node[2])
            code[end] = ("JUMP", len(code))
        else:
            raise ValueError(f"Unknown expression operator: {op!r}")

    emit(ast)
    return code
