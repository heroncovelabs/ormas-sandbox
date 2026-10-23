"""Recursive-descent parser: token stream -> expression tree.

Grammar (lowest to highest precedence)::

    expression := term ((PLUS | MINUS) term)*
    term       := factor ((STAR | SLASH | DSLASH | PERCENT) factor)*
    factor     := (PLUS | MINUS) factor | power
    power      := atom (DSTAR factor)?
    atom       := NUMBER | LPAREN expression RPAREN

Precedence and associativity:

* ``+``, ``-`` are left-associative and lowest.
* ``*``, ``/``, ``//``, ``%`` are left-associative and bind tighter than
  ``+``/``-``.
* Unary ``+``/``-`` bind tighter than the multiplicative operators but looser
  than ``**``, so ``-2 ** 2`` is ``-(2 ** 2)``.
* ``**`` is right-associative and binds tightest. Its exponent is parsed as a
  ``factor``, so signed exponents such as ``2 ** -2`` are valid.
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
        # Additive level: left-fold over term operands.
        node = self.term()
        while self.cur.kind in _ADDITIVE:
            op = _ADDITIVE[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        # Multiplicative level: left-fold over factor operands.
        node = self.factor()
        while self.cur.kind in _MULTIPLICATIVE:
            op = _MULTIPLICATIVE[self.advance().kind]
            node = BinOp(op, node, self.factor())
        return node

    def factor(self) -> Node:
        # Unary sign applies to the following factor, so it binds looser than
        # ``**`` (handled in power) and tighter than ``*``/``/``.
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.factor())
        return self.power()

    def power(self) -> Node:
        # Right-associative: the exponent is a factor, which recurses into
        # power again for chains such as 2 ** 3 ** 2.
        base = self.atom()
        if self.cur.kind == "DSTAR":
            self.advance()
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
