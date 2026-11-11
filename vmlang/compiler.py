"""Lower an expression AST to a flat list of stack-machine instructions.

The instruction set (shared contract with ``vmlang/vm.py``) is documented in the
issue. Each instruction is a tuple ``(OPCODE, *operands)`` where ``OPCODE`` is one
of the uppercase names in that table. Jump operands are absolute indices into the
returned list. Short-circuit ``and``/``or`` and ``if`` require forward jumps whose
targets are only known once the skipped code has been emitted (backpatching).
"""

_BINOPS = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "==": "EQ",
    "<": "LT",
    ">": "GT",
}


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    code = []
    _emit(ast, code)
    return code


def _jump(code, opcode):
    """Emit a jump with a placeholder target; return its index for backpatching."""
    code.append((opcode, None))
    return len(code) - 1


def _patch(code, index):
    """Point the jump at ``index`` to the next instruction to be emitted."""
    code[index] = (code[index][0], len(code))


def _emit(ast, code):
    kind = ast[0]
    if kind == "lit":
        code.append(("PUSH", ast[1]))
    elif kind == "var":
        code.append(("LOAD", ast[1]))
    elif kind == "not":
        _emit(ast[1], code)
        code.append(("NOT",))
    elif kind in _BINOPS:
        _emit(ast[1], code)
        _emit(ast[2], code)
        code.append((_BINOPS[kind],))
    elif kind == "and":
        # a; DUP; JUMP_IF_FALSE end; POP; b; end:
        _emit(ast[1], code)
        code.append(("DUP",))
        to_end = _jump(code, "JUMP_IF_FALSE")
        code.append(("POP",))
        _emit(ast[2], code)
        _patch(code, to_end)
    elif kind == "or":
        # a; DUP; JUMP_IF_FALSE right; JUMP end; right: POP; b; end:
        _emit(ast[1], code)
        code.append(("DUP",))
        to_right = _jump(code, "JUMP_IF_FALSE")
        to_end = _jump(code, "JUMP")
        _patch(code, to_right)
        code.append(("POP",))
        _emit(ast[2], code)
        _patch(code, to_end)
    elif kind == "if":
        # cond; JUMP_IF_FALSE else; then; JUMP end; else: else_; end:
        _emit(ast[1], code)
        to_else = _jump(code, "JUMP_IF_FALSE")
        _emit(ast[2], code)
        to_end = _jump(code, "JUMP")
        _patch(code, to_else)
        _emit(ast[3], code)
        _patch(code, to_end)
    else:
        raise ValueError(f"unknown AST node: {kind!r}")
