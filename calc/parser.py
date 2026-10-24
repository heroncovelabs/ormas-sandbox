"""Recursive-descent parser: token stream -> expression tree.

Grammar (lowest to highest precedence):

    expression : term (('PLUS' | 'MINUS') term)*                 # left-assoc
    term       : factor (('STAR' | 'SLASH' | 'DSLASH' | 'PERCENT') factor)*
                                                                  # left-assoc
    factor     : ('PLUS' | 'MINUS') factor | power              # unary prefix
    power      : atom ['DSTAR' factor]                            # right-assoc
    atom       : NUMBER | 'LPAREN' expression 'RPAREN'

Unary signs bind looser than ``**`` (so ``-2 ** 2 == -4``), while the exponent
of ``**`` is a full factor (so ``2 ** -2`` is valid).
"""

from __future__ import annotations

from calc.ast_nodes import BinOp, Node, Num, UnaryOp
from calc.errors import CalcError
from calc.tokens import Token, tokenize

_ADD_OPS = {"PLUS": "+", "MINUS": "-"}
_MUL_OPS = {
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
        """Addition and subtraction (lowest precedence, left-associative)."""
        node = self.term()
        while self.cur.kind in _ADD_OPS:
            op = _ADD_OPS[self.advance().kind]
            node = BinOp(op, node, self.term())
        return node

    def term(self) -> Node:
        """Multiplication, division, floor division, modulo (left-associative)."""
        node = self.factor()
        while self.cur.kind in _MUL_OPS:
            op = _MUL_OPS[self.advance().kind]
            node = BinOp(op, node, self.factor())
        return node

    def factor(self) -> Node:
        """Unary prefix operators, which bind looser than exponentiation."""
        tok = self.cur
        if tok.kind in _UNARY:
            self.advance()
            return UnaryOp(_UNARY[tok.kind], self.factor())
        return self.power()

    def power(self) -> Node:
        """Exponentiation (right-associative; exponent is a full factor)."""
        node = self.atom()
        if self.cur.kind == "DSTAR":
            self.advance()
            return BinOp("**", node, self.factor())
        return node

    def atom(self) -> Node:
        """Numeric literal or parenthesized expression."""
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
