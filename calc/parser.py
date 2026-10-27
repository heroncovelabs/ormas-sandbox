"""Recursive-descent parser: token stream -> expression tree.

Precedence, lowest to highest: binary ``+ -`` (left), ``* / // %`` (left),
unary ``+ -``, then ``**`` (right-associative; its exponent may be unary).
"""

from __future__ import annotations

from calc.ast_nodes import BinOp, Node, Num, UnaryOp
from calc.errors import CalcError
from calc.tokens import Token, tokenize

_BINOP = {
    "PLUS": "+",
    "MINUS": "-",
    "STAR": "*",
    "SLASH": "/",
    "DSLASH": "//",
    "PERCENT": "%",
    "DSTAR": "**",
}
_ADDITIVE = {"PLUS", "MINUS"}
_MULTIPLICATIVE = {"STAR", "SLASH", "DSLASH", "PERCENT"}
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
        # expression := term (("+" | "-") term)*
        node = self.term()
        while self.cur.kind in _ADDITIVE:
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        # term := unary (("*" | "/" | "//" | "%") unary)*
        node = self.unary()
        while self.cur.kind in _MULTIPLICATIVE:
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.unary())
        return node

    def unary(self) -> Node:
        # unary := ("+" | "-") unary | power
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.unary())
        return self.power()

    def power(self) -> Node:
        # power := atom ("**" unary)?  -- right-associative via unary -> power
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
