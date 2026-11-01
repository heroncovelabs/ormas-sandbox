"""Recursive-descent parser: token stream -> expression tree.

Grammar, lowest to highest precedence:

    expression := term   (('+' | '-') term)*            # left-associative
    term       := factor (('*' | '/' | '//' | '%') factor)*   # left-associative
    factor     := ('+' | '-') factor | power            # unary sign
    power      := atom ('**' factor)?                   # right-associative
    atom       := NUMBER | '(' expression ')'

Because the exponent of ``**`` is a ``factor``, signed exponents such as
``2 ** -2`` are accepted, and because unary signs are parsed above ``power``,
``-2 ** 2`` parses as ``-(2 ** 2)``.
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
        # Level 1: additive operators, left-associative.
        node = self.term()
        while self.cur.kind in _ADDITIVE:
            op = _ADDITIVE[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        # Level 2: multiplicative operators, left-associative.
        node = self.factor()
        while self.cur.kind in _MULTIPLICATIVE:
            op = _MULTIPLICATIVE[self.advance().kind]
            node = BinOp(op, node, self.factor())
        return node

    def factor(self) -> Node:
        # Level 3: unary plus/minus. The operand is a factor, so signs stack
        # and the sign binds looser than ``**``.
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.factor())
        return self.power()

    def power(self) -> Node:
        # Level 4: exponentiation, right-associative. The right operand is a
        # factor, which recurses back into power() for chained exponents.
        node = self.atom()
        if self.cur.kind == "DSTAR":
            self.advance()
            node = BinOp("**", node, self.factor())
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
