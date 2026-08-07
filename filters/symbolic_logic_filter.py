"""
filters/symbolic_logic_filter.py — Moduł Logiki Symbolicznej (v3)

Waliduje formuły logiki zdaniowej w składni z operatorami:
    ¬  (negacja, alias: !)
    ∧  (koniunkcja, alias: &)
    ∨  (alternatywa, alias: |)
    →  (implikacja, alias: ->)
    ↔  (równoważność, alias: <->)
    ⊕  (xor, alias: ^^)

Przykład:  "(A ∧ B) → C"

Nie zależy od pozostałych plików projektu (poza sympy) — może być
używany samodzielnie: `run_formula("(A ∧ B) → C")`.

Zwraca m.in.: listę zmiennych, tabelę prawdy, informację czy formuła
jest tautologią / sprzecznością / spełnialna, oraz postać kanoniczną
(CNF, DNF) wygenerowaną przez sympy — co otwiera drzwi do integracji
z systemami dowodzenia twierdzeń (np. sympy.logic.inference.satisfiable,
albo eksport do formatu DIMACS dla zewnętrznych solverów SAT).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any, Optional

from sympy import symbols as sympy_symbols
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent, Xor, to_cnf, to_dnf
from sympy.logic.inference import satisfiable

# ── Normalizacja operatorów unicode -> tokeny wewnętrzne ────────────────────
_ALIASES = [
    ("<->", "↔"), ("->", "→"), ("^^", "⊕"),
    ("&&", "∧"), ("||", "∨"),
]

_TOKEN_SPEC = [
    ("WS", r"\s+"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("IMPLIES", r"→"),
    ("IFF", r"↔"),
    ("XOR", r"⊕"),
    ("AND", r"[∧&]"),
    ("OR", r"[∨|]"),
    ("NOT", r"[¬!]"),
    ("CONST_T", r"\b(?:True|T|1)\b"),
    ("CONST_F", r"\b(?:False|F|0)\b"),
    ("VAR", r"[A-Za-z][A-Za-z0-9_]*"),
]


class FormulaSyntaxError(Exception):
    def __init__(self, message: str, position: int = -1):
        super().__init__(message)
        self.message = message
        self.position = position


@dataclass
class Token:
    kind: str
    value: str
    pos: int


def _tokenize(text: str) -> list[Token]:
    import re
    for long_form, short_form in _ALIASES:
        text = text.replace(long_form, short_form)

    tokens: list[Token] = []
    i = 0
    n = len(text)
    while i < n:
        for kind, pattern in _TOKEN_SPEC:
            m = re.match(pattern, text[i:])
            if m:
                if kind != "WS":
                    tokens.append(Token(kind, m.group(0), i))
                i += len(m.group(0))
                break
        else:
            raise FormulaSyntaxError(f"nieznany symbol {text[i]!r}", i)
    return tokens


# ── AST ──────────────────────────────────────────────────────────────────
class Node:
    pass


@dataclass
class VarNode(Node):
    name: str


@dataclass
class ConstNode(Node):
    value: bool


@dataclass
class NotNode(Node):
    child: Node


@dataclass
class BinNode(Node):
    op: str  # '∧','∨','→','↔','⊕'
    left: Node
    right: Node


class _Parser:
    """Rekurencyjny parser zejściowy (precedence climbing).

    Priorytety (od najsilniejszego): ¬ > ∧ > ∨ > ⊕ > ↔ > → (prawostronnie łączna)
    """

    def __init__(self, tokens: list[Token], raw: str):
        self.tokens = tokens
        self.raw = raw
        self.i = 0

    def _peek(self) -> Optional[Token]:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _eat(self, kind: str) -> Token:
        tok = self._peek()
        if tok is None or tok.kind != kind:
            got = tok.kind if tok else "EOF"
            pos = tok.pos if tok else len(self.raw)
            raise FormulaSyntaxError(f"oczekiwano {kind}, otrzymano {got}", pos)
        self.i += 1
        return tok

    def parse(self) -> Node:
        node = self._implication()
        if self._peek() is not None:
            raise FormulaSyntaxError("nieoczekiwane dane po formule", self._peek().pos)
        return node

    def _implication(self) -> Node:
        left = self._equivalence()
        tok = self._peek()
        if tok and tok.kind == "IMPLIES":
            self.i += 1
            right = self._implication()  # prawostronna łączność
            return BinNode("→", left, right)
        return left

    def _equivalence(self) -> Node:
        left = self._xor()
        tok = self._peek()
        if tok and tok.kind == "IFF":
            self.i += 1
            right = self._equivalence()
            return BinNode("↔", left, right)
        return left

    def _xor(self) -> Node:
        left = self._disjunction()
        while (tok := self._peek()) and tok.kind == "XOR":
            self.i += 1
            right = self._disjunction()
            left = BinNode("⊕", left, right)
        return left

    def _disjunction(self) -> Node:
        left = self._conjunction()
        while (tok := self._peek()) and tok.kind == "OR":
            self.i += 1
            right = self._conjunction()
            left = BinNode("∨", left, right)
        return left

    def _conjunction(self) -> Node:
        left = self._negation()
        while (tok := self._peek()) and tok.kind == "AND":
            self.i += 1
            right = self._negation()
            left = BinNode("∧", left, right)
        return left

    def _negation(self) -> Node:
        tok = self._peek()
        if tok and tok.kind == "NOT":
            self.i += 1
            return NotNode(self._negation())
        return self._atom()

    def _atom(self) -> Node:
        tok = self._peek()
        if tok is None:
            raise FormulaSyntaxError("nieoczekiwany koniec formuły", len(self.raw))
        if tok.kind == "LPAREN":
            self.i += 1
            node = self._implication()
            self._eat("RPAREN")
            return node
        if tok.kind == "VAR":
            self.i += 1
            return VarNode(tok.value)
        if tok.kind == "CONST_T":
            self.i += 1
            return ConstNode(True)
        if tok.kind == "CONST_F":
            self.i += 1
            return ConstNode(False)
        raise FormulaSyntaxError(f"nieoczekiwany token {tok.kind!r}", tok.pos)


def parse_formula(text: str) -> Node:
    tokens = _tokenize(text)
    if not tokens:
        raise FormulaSyntaxError("pusta formuła", 0)
    return _Parser(tokens, text).parse()


def _collect_vars(node: Node, out: set[str]) -> None:
    if isinstance(node, VarNode):
        out.add(node.name)
    elif isinstance(node, NotNode):
        _collect_vars(node.child, out)
    elif isinstance(node, BinNode):
        _collect_vars(node.left, out)
        _collect_vars(node.right, out)


def _evaluate(node: Node, env: dict[str, bool]) -> bool:
    if isinstance(node, ConstNode):
        return node.value
    if isinstance(node, VarNode):
        return env[node.name]
    if isinstance(node, NotNode):
        return not _evaluate(node.child, env)
    if isinstance(node, BinNode):
        a = _evaluate(node.left, env)
        b = _evaluate(node.right, env)
        if node.op == "∧":
            return a and b
        if node.op == "∨":
            return a or b
        if node.op == "→":
            return (not a) or b
        if node.op == "↔":
            return a == b
        if node.op == "⊕":
            return a != b
    raise ValueError(f"nieznany węzeł AST: {node!r}")


def _to_sympy(node: Node, symtab: dict[str, Any]):
    if isinstance(node, ConstNode):
        return node.value
    if isinstance(node, VarNode):
        return symtab[node.name]
    if isinstance(node, NotNode):
        return Not(_to_sympy(node.child, symtab))
    if isinstance(node, BinNode):
        a = _to_sympy(node.left, symtab)
        b = _to_sympy(node.right, symtab)
        return {
            "∧": And, "∨": Or, "→": Implies, "↔": Equivalent, "⊕": Xor,
        }[node.op](a, b)
    raise ValueError(f"nieznany węzeł AST: {node!r}")


def run_formula(text: str) -> dict:
    """Waliduje formułę logiki zdaniowej i zwraca pełną analizę."""
    try:
        ast = parse_formula(text)
    except FormulaSyntaxError as e:
        snippet = text
        caret = " " * e.position + "^" if e.position >= 0 else ""
        return {
            "status": "error",
            "message": e.message,
            "position": e.position,
            "snippet": snippet,
            "caret": caret,
        }

    var_set: set[str] = set()
    _collect_vars(ast, var_set)
    var_names = sorted(var_set)
    n = len(var_names)

    if n > 20:
        return {
            "status": "error",
            "message": f"zbyt wiele zmiennych ({n}) — tabela prawdy 2^{n} wierszy jest niepraktyczna",
        }

    rows = []
    for combo in product([False, True], repeat=n):
        env = dict(zip(var_names, combo))
        rows.append({"assignment": env, "result": _evaluate(ast, env)})

    all_true = all(r["result"] for r in rows) if rows else True
    all_false = all(not r["result"] for r in rows) if rows else True

    symtab = {name: sympy_symbols(name) for name in var_names}
    sym_expr = _to_sympy(ast, symtab)

    try:
        cnf = str(to_cnf(sym_expr, simplify=True))
    except Exception:
        cnf = None
    try:
        dnf = str(to_dnf(sym_expr, simplify=True))
    except Exception:
        dnf = None

    is_satisfiable = bool(satisfiable(sym_expr))

    return {
        "status": "ok",
        "formula": text,
        "variables": var_names,
        "num_variables": n,
        "truth_table": rows,
        "is_tautology": all_true,
        "is_contradiction": all_false,
        "is_satisfiable": is_satisfiable,
        "cnf": cnf,
        "dnf": dnf,
        "sympy_repr": str(sym_expr),
    }


def run(p) -> dict:
    """Zgodność z konwencją filters/*.run(ParsedExpr). Używa p.raw jako formuły."""
    raw = getattr(p, "raw", None) or getattr(p, "expr", None) or str(p)
    return run_formula(raw)
