"""Recursive-descent parser: token stream -> expression tree.

Precedence, lowest to highest:

    1. ``+`` ``-``               (left associative)
    2. ``*`` ``/`` ``//`` ``%``  (left associative)
    3. unary ``+`` ``-``
    4. ``**``                    (right associative)

Unary operators bind looser than ``**`` so ``-2 ** 2 == -(2 ** 2)``, while the
right operand of ``**`` is parsed at the unary level so ``2 ** -2`` is valid.
"""

from __future__ import annotations

from calc.ast_nodes import BinOp, Node, Num, UnaryOp
from calc.errors import CalcError
from calc.tokens import Token, tokenize

_ADDITIVE = {"PLUS": "+", "MINUS": "-"}
_MULTIPLICATIVE = {
    "STAR": "*",
    "SLASH": "/",
    "DSLASH": "//",
    "PERCENT": "%",
}
_UNARY = {"PLUS": "+", "MINUS": "-"}


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

    def expression(self) -> Node:
        """Additive level: left-associative ``+`` and ``-``."""
        node = self.term()
        while self.cur.kind in _ADDITIVE:
            op = _ADDITIVE[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        """Multiplicative level: left-associative ``*``, ``/``, ``//``, ``%``."""
        node = self.unary()
        while self.cur.kind in _MULTIPLICATIVE:
            op = _MULTIPLICATIVE[self.advance().kind]
            node = BinOp(op, node, self.unary())
        return node

    def unary(self) -> Node:
        """Unary level: prefix ``+``/``-`` applied to a power expression."""
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.unary())
        return self.power()

    def power(self) -> Node:
        """Power level: right-associative ``**`` over atoms."""
        node = self.atom()
        if self.cur.kind == "DSTAR":
            self.advance()
            node = BinOp("**", node, self.unary())
        return node

    def atom(self) -> Node:
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
