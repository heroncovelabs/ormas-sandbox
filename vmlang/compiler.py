"""Lower an expression AST to a flat list of stack-machine instructions.

The instruction set (shared contract with ``vmlang/vm.py``) is documented in the
issue. Each instruction is a tuple ``(OPCODE, *operands)`` where ``OPCODE`` is one
of the uppercase names in that table. Jump operands are absolute indices into the
returned list. Short-circuit ``and``/``or`` and ``if`` require forward jumps whose
targets are only known once the skipped code has been emitted (backpatching).
"""

_BINARY = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "==": "EQ",
    "<": "LT",
    ">": "GT",
}


def _emit(code, ast):
    """Append instructions computing ``ast`` onto ``code`` and return ``code``."""
    op = ast[0]

    if op == "lit":
        code.append(("PUSH", ast[1]))
    elif op == "var":
        code.append(("LOAD", ast[1]))
    elif op == "not":
        _emit(code, ast[1])
        code.append(("NOT",))
    elif op in _BINARY:
        _emit(code, ast[1])
        _emit(code, ast[2])
        code.append((_BINARY[op],))
    elif op == "and":
        _emit(code, ast[1])
        code.append(("DUP",))
        jf = len(code)
        code.append(("JUMP_IF_FALSE", None))  # keep falsy left value
        code.append(("POP",))
        _emit(code, ast[2])
        code[jf] = ("JUMP_IF_FALSE", len(code))
    elif op == "or":
        _emit(code, ast[1])
        code.append(("DUP",))
        jf = len(code)
        code.append(("JUMP_IF_FALSE", None))  # falsy: discard and evaluate right
        end = len(code)
        code.append(("JUMP", None))  # truthy: keep left value
        code[jf] = ("JUMP_IF_FALSE", len(code))
        code.append(("POP",))
        _emit(code, ast[2])
        code[end] = ("JUMP", len(code))
    elif op == "if":
        _emit(code, ast[1])
        jf = len(code)
        code.append(("JUMP_IF_FALSE", None))
        _emit(code, ast[2])
        jmp = len(code)
        code.append(("JUMP", None))
        code[jf] = ("JUMP_IF_FALSE", len(code))
        _emit(code, ast[3])
        code[jmp] = ("JUMP", len(code))
    else:
        raise ValueError(f"unknown AST node: {op!r}")

    return code


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    return _emit([], ast)
