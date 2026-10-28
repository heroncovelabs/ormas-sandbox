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
    _compile(ast, code)
    return code


def _emit(code, opcode, *operands):
    """Append an instruction and return its absolute index."""
    code.append((opcode,) + operands)
    return len(code) - 1


def _patch(code, index, target):
    """Rewrite the jump operand of the instruction at ``index``."""
    instr = code[index]
    code[index] = (instr[0], target)


def _compile(ast, code):
    """Emit instructions for ``ast`` onto ``code``, leaving one value on the stack."""
    if not isinstance(ast, tuple) or not ast:
        raise ValueError("malformed AST node: %r" % (ast,))

    head = ast[0]

    if head == "lit":
        _emit(code, "PUSH", ast[1])
    elif head == "var":
        _emit(code, "LOAD", ast[1])
    elif head == "not":
        _compile(ast[1], code)
        _emit(code, "NOT")
    elif head in _BINOPS:
        _compile(ast[1], code)
        _compile(ast[2], code)
        _emit(code, _BINOPS[head])
    elif head == "and":
        # Left value: keep it if falsy, drop it and evaluate the right side.
        _compile(ast[1], code)
        _emit(code, "DUP")
        jump = _emit(code, "JUMP_IF_FALSE", None)
        _emit(code, "POP")
        _compile(ast[2], code)
        _patch(code, jump, len(code))
    elif head == "or":
        # Left value: keep it if truthy, drop it and evaluate the right side.
        _compile(ast[1], code)
        _emit(code, "DUP")
        _emit(code, "NOT")
        jump = _emit(code, "JUMP_IF_FALSE", None)
        _emit(code, "POP")
        _compile(ast[2], code)
        _patch(code, jump, len(code))
    elif head == "if":
        _compile(ast[1], code)
        else_jump = _emit(code, "JUMP_IF_FALSE", None)
        _compile(ast[2], code)
        end_jump = _emit(code, "JUMP", None)
        _patch(code, else_jump, len(code))
        _compile(ast[3], code)
        _patch(code, end_jump, len(code))
    else:
        raise ValueError("unknown AST node: %r" % (head,))
