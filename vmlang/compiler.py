"""Lower an expression AST to a flat list of stack-machine instructions.

The instruction set (shared contract with ``vmlang/vm.py``) is documented in the
issue. Each instruction is a tuple ``(OPCODE, *operands)`` where ``OPCODE`` is one
of the uppercase names in that table. Jump operands are absolute indices into the
returned list. Short-circuit ``and``/``or`` and ``if`` require forward jumps whose
targets are only known once the skipped code has been emitted (backpatching).
"""


_BINARY_OPS = {
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


def _emit(node, code):
    """Append instructions for ``node`` to the shared list ``code``."""
    kind = node[0]
    if kind == "lit":
        code.append(("PUSH", node[1]))
    elif kind == "var":
        code.append(("LOAD", node[1]))
    elif kind == "not":
        _emit(node[1], code)
        code.append(("NOT",))
    elif kind in _BINARY_OPS:
        _emit(node[1], code)
        _emit(node[2], code)
        code.append((_BINARY_OPS[kind],))
    elif kind == "and":
        # left; DUP; JUMP_IF_FALSE end; POP; right; end:
        _emit(node[1], code)
        code.append(("DUP",))
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(node[2], code)
        code[jif] = ("JUMP_IF_FALSE", len(code))
    elif kind == "or":
        # left; DUP; JUMP_IF_FALSE right_start; JUMP end; right_start: POP; right; end:
        _emit(node[1], code)
        code.append(("DUP",))
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        jump = len(code)
        code.append(("JUMP", None))
        right_start = len(code)
        code.append(("POP",))
        _emit(node[2], code)
        code[jif] = ("JUMP_IF_FALSE", right_start)
        code[jump] = ("JUMP", len(code))
    elif kind == "if":
        # cond; JUMP_IF_FALSE else_start; then; JUMP end; else_start: else; end:
        _emit(node[1], code)
        jif = len(code)
        code.append(("JUMP_IF_FALSE", None))
        _emit(node[2], code)
        jump = len(code)
        code.append(("JUMP", None))
        else_start = len(code)
        _emit(node[3], code)
        code[jif] = ("JUMP_IF_FALSE", else_start)
        code[jump] = ("JUMP", len(code))
    else:
        raise ValueError(f"unknown AST node: {kind!r}")
