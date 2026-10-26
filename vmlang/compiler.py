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


def _emit(ast, code):
    """Append the instructions for ``ast`` to the flat list ``code``."""
    if not isinstance(ast, tuple) or not ast:
        raise ValueError(f"malformed AST node: {ast!r}")

    op = ast[0]

    if op == "lit":
        code.append(("PUSH", ast[1]))
    elif op == "var":
        code.append(("LOAD", ast[1]))
    elif op == "not":
        _emit(ast[1], code)
        code.append(("NOT",))
    elif op in _BINARY_OPS:
        _emit(ast[1], code)
        _emit(ast[2], code)
        code.append((_BINARY_OPS[op],))
    elif op == "and":
        # left; DUP; JUMP_IF_FALSE end; POP; right
        _emit(ast[1], code)
        code.append(("DUP",))
        patch = len(code)
        code.append(("JUMP_IF_FALSE", None))
        code.append(("POP",))
        _emit(ast[2], code)
        code[patch] = ("JUMP_IF_FALSE", len(code))
    elif op == "or":
        # left; DUP; JUMP_IF_FALSE keep; JUMP end; keep: POP; right
        _emit(ast[1], code)
        code.append(("DUP",))
        patch_false = len(code)
        code.append(("JUMP_IF_FALSE", None))
        patch_jump = len(code)
        code.append(("JUMP", None))
        keep = len(code)
        code.append(("POP",))
        _emit(ast[2], code)
        code[patch_false] = ("JUMP_IF_FALSE", keep)
        code[patch_jump] = ("JUMP", len(code))
    elif op == "if":
        # cond; JUMP_IF_FALSE else_start; then; JUMP end; else_start: else
        _emit(ast[1], code)
        patch_false = len(code)
        code.append(("JUMP_IF_FALSE", None))
        _emit(ast[2], code)
        patch_jump = len(code)
        code.append(("JUMP", None))
        else_start = len(code)
        _emit(ast[3], code)
        code[patch_false] = ("JUMP_IF_FALSE", else_start)
        code[patch_jump] = ("JUMP", len(code))
    else:
        raise ValueError(f"unknown AST node type: {op!r}")
