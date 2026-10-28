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


def _patch(code, at, target):
    code[at] = (code[at][0], target)


def _emit(node, code):
    kind = node[0]
    if kind == "lit":
        code.append(("PUSH", node[1]))
    elif kind == "var":
        code.append(("LOAD", node[1]))
    elif kind == "not":
        _emit(node[1], code)
        code.append(("NOT",))
    elif kind in _BINOPS:
        _emit(node[1], code)
        _emit(node[2], code)
        code.append((_BINOPS[kind],))
    elif kind == "and":
        # a; DUP; JUMP_IF_FALSE end; POP; b; end:
        _emit(node[1], code)
        code.append(("DUP",))
        jf = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(node[2], code)
        _patch(code, jf, len(code))
    elif kind == "or":
        # a; DUP; JUMP_IF_FALSE right; JUMP end; right: POP; b; end:
        _emit(node[1], code)
        code.append(("DUP",))
        jf = len(code)
        code.append(("JUMP_IF_FALSE", None))
        j = len(code)
        code.append(("JUMP", None))
        _patch(code, jf, len(code))
        code.append(("POP",))
        _emit(node[2], code)
        _patch(code, j, len(code))
    elif kind == "if":
        # cond; JUMP_IF_FALSE else; then; JUMP end; else: else_; end:
        _emit(node[1], code)
        jf = len(code)
        code.append(("JUMP_IF_FALSE", None))
        _emit(node[2], code)
        j = len(code)
        code.append(("JUMP", None))
        _patch(code, jf, len(code))
        _emit(node[3], code)
        _patch(code, j, len(code))
    else:
        raise ValueError(f"unknown AST node: {kind!r}")
