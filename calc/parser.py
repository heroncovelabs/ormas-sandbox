"""Recursive-descent parser: token stream -> expression tree.

Grammar (lowest to highest precedence):

    expression := term (("+" | "-") term)*        # left-associative
    term       := power (("*" | "/" | "//" | "%") power)*  # left-associative
    unary      := ("+" | "-") unary | power
    power      := atom ("**" unary)?              # right-associative
    atom       := NUMBER | "(" expression ")"

Unary ``+``/``-`` bind tighter than the binary operators but looser than
``**``, so ``-2 ** 2 == -(2 ** 2)`` while ``2 ** -2`` is valid.
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
        node = self.term()
        while self.cur.kind in _ADDITIVE:
            op = _ADDITIVE[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        node = self.unary()
        while self.cur.kind in _MULTIPLICATIVE:
            op = _MULTIPLICATIVE[self.advance().kind]
            node = BinOp(op, node, self.unary())
        return node

    def unary(self) -> Node:
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.unary())
        return self.power()

    def power(self) -> Node:
        base = self.atom()
        if self.cur.kind == "DSTAR":
            self.advance()
            return BinOp("**", base, self.unary())
        return base

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
