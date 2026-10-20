"""Lower an expression AST to a flat list of stack-machine instructions.

The instruction set (shared contract with ``vmlang/vm.py``) is documented in the
issue. Each instruction is a tuple ``(OPCODE, *operands)`` where ``OPCODE`` is one
of the uppercase names in that table. Jump operands are absolute indices into the
returned list. Short-circuit ``and``/``or`` and ``if`` require forward jumps whose
targets are only known once the skipped code has been emitted (backpatching).
"""


_BINARY_OPS = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
               "==": "EQ", "<": "LT", ">": "GT"}


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    code = []
    _emit_node(ast, code)
    return code


def _emit_node(node, code):
    kind = node[0]
    if kind == "lit":
        code.append(("PUSH", node[1]))
    elif kind == "var":
        code.append(("LOAD", node[1]))
    elif kind == "not":
        _emit_node(node[1], code)
        code.append(("NOT",))
    elif kind in _BINARY_OPS:
        _emit_node(node[1], code)
        _emit_node(node[2], code)
        code.append((_BINARY_OPS[kind],))
    elif kind == "and":
        # left; DUP; JUMP_IF_FALSE end (keeps left when falsy); POP; right; end:
        _emit_node(node[1], code)
        code.append(("DUP",))
        jump = _emit_placeholder(code, "JUMP_IF_FALSE")
        code.append(("POP",))
        _emit_node(node[2], code)
        _patch(code, jump, len(code))
    elif kind == "or":
        # left; DUP; NOT; JUMP_IF_FALSE end (keeps left when truthy); POP; right; end:
        _emit_node(node[1], code)
        code.append(("DUP",))
        code.append(("NOT",))
        jump = _emit_placeholder(code, "JUMP_IF_FALSE")
        code.append(("POP",))
        _emit_node(node[2], code)
        _patch(code, jump, len(code))
    elif kind == "if":
        # cond; JUMP_IF_FALSE else; then; JUMP end; else: else_branch; end:
        _emit_node(node[1], code)
        to_else = _emit_placeholder(code, "JUMP_IF_FALSE")
        _emit_node(node[2], code)
        to_end = _emit_placeholder(code, "JUMP")
        _patch(code, to_else, len(code))
        _emit_node(node[3], code)
        _patch(code, to_end, len(code))
    else:
        raise ValueError(f"unknown AST node {kind!r}")


def _emit_placeholder(code, opcode):
    """Emit a forward jump whose absolute target is filled in later; return its index."""
    code.append((opcode, None))
    return len(code) - 1


def _patch(code, index, target):
    code[index] = (code[index][0], target)
