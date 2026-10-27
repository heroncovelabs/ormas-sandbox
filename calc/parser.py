"""Recursive-descent parser: token stream -> expression tree.

Grammar (lowest to highest precedence):

    expression := term (('+' | '-') term)*          # left-associative
    term       := factor (('*' | '/' | '//' | '%') factor)*   # left-associative
    factor     := ('+' | '-') factor | power        # unary sign
    power      := atom ('**' factor)?               # right-associative
    atom       := NUMBER | '(' expression ')'

Consequences: ``2 + 3 * 4 == 14``, ``2 ** 3 ** 2 == 512``, ``-2 ** 2 == -4``,
and ``2 ** -2 == 0.25`` because the exponent is a unary factor.
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
        # Lowest precedence: additive operators, folded left-associatively.
        node = self.term()
        while self.cur.kind in ("PLUS", "MINUS"):
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        # Multiplicative operators, folded left-associatively.
        node = self.factor()
        while self.cur.kind in ("STAR", "SLASH", "DSLASH", "PERCENT"):
            op = _BINOP[self.advance().kind]
            node = BinOp(op, node, self.factor())
        return node

    def factor(self) -> Node:
        # Unary sign binds tighter than * / // % but looser than **, so the
        # operand is parsed as a factor (recursively) and then as a power.
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.factor())
        return self.power()

    def power(self) -> Node:
        # Exponentiation is right-associative: the right operand is a factor,
        # which allows signed exponents such as 2 ** -2 and recurses into
        # further ** for 2 ** 3 ** 2 == 2 ** (3 ** 2).
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
            # Parentheses reset precedence and invoke the full grammar.
            node = self.expression()
            if self.cur.kind != "RPAREN":
                raise CalcError("expected ')'")
            self.advance()
            return node
        raise CalcError(f"unexpected token {tok.value!r}")


def parse(text: str) -> Node:
    return _Parser(tokenize(text)).parse()
