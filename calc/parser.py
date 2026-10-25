"""Recursive-descent parser honoring arithmetic precedence and associativity."""

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
        while self.cur.kind in ("PLUS", "MINUS"):
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        node = self.factor()
        while self.cur.kind in ("STAR", "SLASH", "DSLASH", "PERCENT"):
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.factor())
        return node

    def factor(self) -> Node:
        if self.cur.kind in _UNARY:
            op = _UNARY[self.advance().kind]
            return UnaryOp(op, self.factor())
        return self.power()

    def power(self) -> Node:
        node = self.atom()
        if self.cur.kind == "DSTAR":
            op = _BINOP[self.advance().kind]
            # A unary factor permits signed exponents and nests powers rightward.
            node = BinOp(op, node, self.factor())
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
