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


def _emit(code, ast):
    kind = ast[0]
    if kind == "lit":
        code.append(("PUSH", ast[1]))
    elif kind == "var":
        code.append(("LOAD", ast[1]))
    elif kind == "not":
        _emit(code, ast[1])
        code.append(("NOT",))
    elif kind in _BINOPS:
        _emit(code, ast[1])
        _emit(code, ast[2])
        code.append((_BINOPS[kind],))
    elif kind == "and":
        # a; DUP; JIF end (keeps a if falsy); else drop a and yield b.
        _emit(code, ast[1])
        code.append(("DUP",))
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(code, ast[2])
        code[jif] = ("JUMP_IF_FALSE", len(code))
    elif kind == "or":
        # a; DUP; NOT; JIF end (jumps when a is truthy, keeping a); else drop a.
        _emit(code, ast[1])
        code.append(("DUP",))
        code.append(("NOT",))
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(code, ast[2])
        code[jif] = ("JUMP_IF_FALSE", len(code))
    elif kind == "if":
        _emit(code, ast[1])
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        _emit(code, ast[2])
        jump = len(code)
        code.append(("JUMP", None))
        code[jif] = ("JUMP_IF_FALSE", len(code))
        _emit(code, ast[3])
        code[jump] = ("JUMP", len(code))
    else:
        raise ValueError("unknown AST node: %r" % (kind,))


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    code = []
    _emit(code, ast)
    return code
