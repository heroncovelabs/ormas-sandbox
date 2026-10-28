"""Recursive-descent parser: token stream -> expression tree.

Grammar, lowest to highest precedence:

    expression := term ((PLUS | MINUS) term)*           # left-associative
    term       := factor ((STAR | SLASH | DSLASH | PERCENT) factor)*  # left-assoc.
    factor     := (PLUS | MINUS) factor | power         # unary prefix
    power      := atom (DSTAR factor)?                  # right-associative
    atom       := NUMBER | LPAREN expression RPAREN

Unary minus binds looser than ``**`` (so ``-2 ** 2`` is ``-(2 ** 2)``), while
the exponent of ``**`` is a full factor (so ``2 ** -2`` is valid).
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
_ADD_OPS = ("PLUS", "MINUS")
_MUL_OPS = ("STAR", "SLASH", "DSLASH", "PERCENT")
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
        while self.cur.kind in _ADD_OPS:
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        node = self.factor()
        while self.cur.kind in _MUL_OPS:
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.factor())
        return node

    def factor(self) -> Node:
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.factor())
        return self.power()

    def power(self) -> Node:
        base = self.atom()
        if self.cur.kind == "DSTAR":
            self.advance()
            # The exponent is a factor: it allows signed exponents and, via
            # recursion through power(), makes ** right-associative.
            return BinOp("**", base, self.factor())
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
