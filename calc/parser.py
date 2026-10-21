"""Recursive-descent parser: token stream -> expression tree.

Grammar, lowest precedence first:

    expression := term   (('+' | '-') term)*          left-associative
    term       := unary  (('*' | '/' | '//' | '%') unary)*   left-associative
    unary      := ('+' | '-') unary | power           unary binds looser than **
    power      := primary ('**' unary)?              right-associative
    primary    := NUMBER | '(' expression ')'

The exponent of ``**`` is a ``unary`` production, so ``2 ** -2`` is valid while
``-2 ** 2`` parses as ``-(2 ** 2)``.
"""

from __future__ import annotations

from calc.ast_nodes import BinOp, Node, Num, UnaryOp
from calc.errors import CalcError
from calc.tokens import Token, tokenize

_ADD_OPS = {"PLUS": "+", "MINUS": "-"}
_MUL_OPS = {"STAR": "*", "SLASH": "/", "DSLASH": "//", "PERCENT": "%"}
_UNARY_OPS = {"PLUS": "+", "MINUS": "-"}


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    @property
    def cur(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse(self) -> Node:
        if self.cur.kind == "EOF":
            raise CalcError("empty expression")
        node = self.expression()
        if self.cur.kind != "EOF":
            raise CalcError(f"unexpected trailing token {self.cur.value!r}")
        return node

    # Level 1: binary + and -, left-associative.
    def expression(self) -> Node:
        node = self.term()
        while self.cur.kind in _ADD_OPS:
            op = _ADD_OPS[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    # Level 2: binary *, /, //, %, left-associative.
    def term(self) -> Node:
        node = self.unary()
        while self.cur.kind in _MUL_OPS:
            op = _MUL_OPS[self.advance().kind]
            node = BinOp(op, node, self.unary())
        return node

    # Level 3: prefix + and -. Binds tighter than the binary operators above
    # but looser than **, so -2 ** 2 is -(2 ** 2).
    def unary(self) -> Node:
        tok = self.cur
        if tok.kind in _UNARY_OPS:
            self.advance()
            return UnaryOp(_UNARY_OPS[tok.kind], self.unary())
        return self.power()

    # Level 4: **, right-associative. The exponent is a unary factor, so
    # 2 ** 3 ** 2 == 2 ** (3 ** 2) and 2 ** -2 is valid.
    def power(self) -> Node:
        base = self.primary()
        if self.cur.kind == "DSTAR":
            self.advance()
            return BinOp("**", base, self.unary())
        return base

    def primary(self) -> Node:
        tok = self.cur
        if tok.kind == "NUMBER":
            self.advance()
            return Num(tok.value)
        if tok.kind == "LPAREN":
            self.advance()
            node = self.expression()
            if self.cur.kind != "RPAREN":
                raise CalcError("expected ')'")
            self.advance()
            return node
        raise CalcError(f"unexpected token {tok.value!r}")


def parse(text: str) -> Node:
    return _Parser(tokenize(text)).parse()
