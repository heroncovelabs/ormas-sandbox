"""Recursive-descent parser: token stream -> expression tree.

Grammar, lowest to highest precedence:

    expression : term (('+' | '-') term)*
    term       : unary (('*' | '/' | '//' | '%') unary)*
    unary      : ('+' | '-') unary | power
    power      : atom ('**' unary)?
    atom       : NUMBER | '(' expression ')'

``**`` is right-associative and binds tighter than every binary operator.
Unary ``+``/``-`` bind looser than ``**`` but tighter than the multiplicative
operators, so ``-2 ** 2`` parses as ``-(2 ** 2)`` while ``2 ** -2`` remains
valid.
"""

from __future__ import annotations

from calc.ast_nodes import BinOp, Node, Num, UnaryOp
from calc.errors import CalcError
from calc.tokens import Token, tokenize

_ADDITIVE = {"PLUS": "+", "MINUS": "-"}
_MULTIPLICATIVE = {"STAR": "*", "SLASH": "/", "DSLASH": "//", "PERCENT": "%"}
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
        # Level 1: binary + and -, left-associative.
        node = self.term()
        while self.cur.kind in _ADDITIVE:
            op = _ADDITIVE[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        # Level 2: binary *, /, //, %, left-associative.
        node = self.unary()
        while self.cur.kind in _MULTIPLICATIVE:
            op = _MULTIPLICATIVE[self.advance().kind]
            node = BinOp(op, node, self.unary())
        return node

    def unary(self) -> Node:
        # Level 3: unary + and -, binding tighter than the binary operators
        # above but looser than **, so the operand is a full power
        # expression: -2 ** 2 == -(2 ** 2).
        if self.cur.kind in _UNARY:
            op = _UNARY[self.advance().kind]
            return UnaryOp(op, self.unary())
        return self.power()

    def power(self) -> Node:
        # Level 4 (highest): **, right-associative. The base is a bare atom
        # (unary operators stay below **), while the exponent recurses through
        # unary() so 2 ** -2 and 2 ** 3 ** 2 == 2 ** (3 ** 2) both parse.
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
