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


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    code = []
    _emit(ast, code)
    return code


def _emit(node, code):
    kind = node[0]
    if kind == "lit":
        code.append(("PUSH", node[1]))
    elif kind == "var":
        code.append(("LOAD", node[1]))
    elif kind == "not":
        _emit(node[1], code)
        code.append(("NOT",))
    elif kind in _BINARY:
        _emit(node[1], code)
        _emit(node[2], code)
        code.append((_BINARY[kind],))
    elif kind == "and":
        # Left falsy -> keep left as the result and skip right.
        _emit(node[1], code)
        code.append(("DUP",))
        jump = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(node[2], code)
        code[jump] = ("JUMP_IF_FALSE", len(code))
    elif kind == "or":
        # Left truthy -> keep left as the result and skip right.
        _emit(node[1], code)
        code.append(("DUP",))
        code.append(("NOT",))
        jump = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(node[2], code)
        code[jump] = ("JUMP_IF_FALSE", len(code))
    elif kind == "if":
        _emit(node[1], code)
        to_else = len(code)
        code.append(("JUMP_IF_FALSE", None))
        _emit(node[2], code)
        to_end = len(code)
        code.append(("JUMP", None))
        code[to_else] = ("JUMP_IF_FALSE", len(code))
        _emit(node[3], code)
        code[to_end] = ("JUMP", len(code))
    else:
        raise ValueError(f"unknown AST node: {kind!r}")
