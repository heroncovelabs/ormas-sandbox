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
        # left; DUP; JIF end (keeps left if falsy); else POP and evaluate right
        _emit(ast[1], code)
        code.append(("DUP",))
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(ast[2], code)
        code[jif] = ("JUMP_IF_FALSE", len(code))
    elif kind == "or":
        # left; DUP; NOT; JIF end (keeps left if truthy); else POP and evaluate right
        _emit(ast[1], code)
        code.append(("DUP",))
        code.append(("NOT",))
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(ast[2], code)
        code[jif] = ("JUMP_IF_FALSE", len(code))
    elif kind == "if":
        _emit(ast[1], code)
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        _emit(ast[2], code)
        jmp = len(code)
        code.append(("JUMP", None))
        code[jif] = ("JUMP_IF_FALSE", len(code))
        _emit(ast[3], code)
        code[jmp] = ("JUMP", len(code))
    else:
        raise ValueError(f"unknown AST node: {kind!r}")


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    code = []
    _emit(ast, code)
    return code
