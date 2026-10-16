"""Recursive-descent parser: token stream -> expression tree.

Grammar (lowest to highest precedence)::

    expression := term (('+' | '-') term)*          # left-associative
    term       := factor (('*' | '/' | '//' | '%') factor)*   # left-associative
    factor     := ('+' | '-') factor | power        # unary sign
    power      := atom ('**' factor)?               # right-associative
    atom       := NUMBER | '(' expression ')'

Consequences:
  * ``2 + 3 * 4``   parses as ``2 + (3 * 4)``.
  * ``2 ** 3 ** 2`` parses as ``2 ** (3 ** 2)``.
  * ``-2 ** 2``     parses as ``-(2 ** 2)``.
  * ``2 ** -2``     is valid, because the exponent is a unary factor.
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
_ADD_KINDS = ("PLUS", "MINUS")
_MUL_KINDS = ("STAR", "SLASH", "DSLASH", "PERCENT")
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
        """Additive level: left-folded ``+`` and ``-`` over terms."""
        node = self.term()
        while self.cur.kind in _ADD_KINDS:
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        """Multiplicative level: left-folded ``*``, ``/``, ``//``, ``%`` over factors."""
        node = self.factor()
        while self.cur.kind in _MUL_KINDS:
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.factor())
        return node

    def factor(self) -> Node:
        """Unary sign level: prefix ``+``/``-`` applied to a factor, else a power."""
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.factor())
        return self.power()

    def power(self) -> Node:
        """Exponent level: ``atom ** factor``, right-associative."""
        base = self.atom()
        if self.cur.kind == "DSTAR":
            self.advance()
            return BinOp("**", base, self.factor())
        return base

    def atom(self) -> Node:
        """Numbers and parenthesized full expressions."""
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
