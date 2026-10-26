"""Lower an expression AST to a flat list of stack-machine instructions.

The instruction set (shared contract with ``vmlang/vm.py``) is documented in the
issue. Each instruction is a tuple ``(OPCODE, *operands)`` where ``OPCODE`` is one
of the uppercase names in that table. Jump operands are absolute indices into the
returned list. Short-circuit ``and``/``or`` and ``if`` require forward jumps whose
targets are only known once the skipped code has been emitted (backpatching).
"""

_ARITH = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}
_COMPARE = {"==": "EQ", "<": "LT", ">": "GT"}
_BINARY = {**_ARITH, **_COMPARE}


def compile_expr(ast):
    """Return a flat list of instructions that computes ``ast`` on the VM stack."""
    code = []
    _emit(ast, code)
    return code


def _emit(node, code):
    """Append the instructions computing ``node`` to ``code`` in place."""
    if not isinstance(node, tuple) or not node:
        raise ValueError(f"bad AST node: {node!r}")
    op = node[0]

    if op == "lit":
        (value,) = node[1:]
        code.append(("PUSH", value))
    elif op == "var":
        (name,) = node[1:]
        code.append(("LOAD", name))
    elif op == "not":
        (operand,) = node[1:]
        _emit(operand, code)
        code.append(("NOT",))
    elif op in _BINARY:
        _, left, right = node
        _emit(left, code)
        _emit(right, code)
        code.append((_BINARY[op],))
    elif op == "and":
        _, left, right = node
        _emit(left, code)                    # left operand's value
        code.append(("DUP",))                # a copy drives the jump test
        test = len(code)
        code.append(("JUMP_IF_FALSE", None))  # placeholder: popped by the jump
        code.append(("POP",))                # truthy left: drop the kept copy
        _emit(right, code)                   # result is the right operand
        code[test] = ("JUMP_IF_FALSE", len(code))  # backpatch: falsy -> keep left
    elif op == "or":
        _, left, right = node
        _emit(left, code)                    # left operand's value
        code.append(("DUP",))                # a copy drives the jump test
        test = len(code)
        code.append(("JUMP_IF_FALSE", None))  # falsy left: fall through to right
        keep = len(code)
        code.append(("JUMP", None))          # truthy left: keep it, skip right
        code[test] = ("JUMP_IF_FALSE", len(code))  # backpatch: falsy -> run right
        _emit(right, code)                   # result is the right operand
        code[keep] = ("JUMP", len(code))     # backpatch: truthy -> done
    elif op == "if":
        _, cond, then, otherwise = node
        _emit(cond, code)
        test = len(code)
        code.append(("JUMP_IF_FALSE", None))  # placeholder: falsy -> else branch
        _emit(then, code)                    # only the taken branch runs
        end = len(code)
        code.append(("JUMP", None))          # placeholder: skip the else branch
        code[test] = ("JUMP_IF_FALSE", len(code))  # backpatch: falsy -> else
        _emit(otherwise, code)
        code[end] = ("JUMP", len(code))      # backpatch: then done -> end
    else:
        raise ValueError(f"unknown AST node: {op!r}")
