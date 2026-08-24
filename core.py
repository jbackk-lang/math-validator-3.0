"""
core.py — jedyne miejsce gdzie sympify() jest wywoływane.
Parsuje wyrażenie raz i zwraca ParsedExpr przekazywany do wszystkich filtrów.

Poprawki v2:
  1. Guard dla pustego stringa → ParsedExpr z error="empty expression"
     (oryginał: IndexError: list index out of range)
  2. Guard dla () i podobnych → tuple nie ma is_number
     (oryginał: AttributeError: 'tuple' object has no attribute 'is_number')
  3. ParsedExpr.sym_raw eksponuje nieewaluowane wyrażenie (dostępne od v1,
     ale teraz jawnie dokumentowane — filtry powinny go używać dla domeny)
"""

from sympy import sympify, symbols, zoo, oo, nan, sin, cos, tan
from dataclasses import dataclass, field
from typing import Any, Optional
import re

x = symbols("x")

# Wyrażenia które sympify() akceptuje ale nie są wyrażeniami matematycznymi
_REJECTED_STRINGS = {"", "()", "[]", "{}"}


@dataclass
class ParsedExpr:
    raw:          str
    sym:          Any  = None   # wyrażenie zewaluowane
    sym_raw:      Any  = None   # wyrażenie NIEzewaluowane (do analizy domeny)
    x:            Any  = None
    is_zoo:       bool = False
    is_const:     bool = False
    has_division: bool = False
    cycles:       int  = 0
    fractions:    int  = 0
    powers:       int  = 0
    has_trig:     bool = False
    trig_count:   int  = 0
    has_pi:       bool = False
    error:        str  = ""

    def __post_init__(self):
        self.x = x

    @property
    def ok(self) -> bool:
        return not self.error and self.sym is not None


def parse(expr: str) -> "ParsedExpr":
    """
    Parsuje wyrażenie RAZ. Wynik przekazywany do wszystkich filtrów.

    Poprawki względem oryginału:
    - expr="" → ParsedExpr(error="empty expression") zamiast IndexError
    - expr="()" → ParsedExpr(error="empty parens") zamiast AttributeError
    - ogólny guard: jeśli sympify zwróci tuple/set/list → błąd zamiast crashu
    """
    # ── GUARD 1: pusty string ────────────────────────────────────────────────
    if not expr or not expr.strip():
        return ParsedExpr(raw=expr, error="empty expression")

    # ── GUARD 2: jawnie odrzucone wzorce ─────────────────────────────────────
    if expr.strip() in _REJECTED_STRINGS:
        return ParsedExpr(raw=expr, error=f"rejected pattern: {expr.strip()!r}")

    try:
        sym_raw = sympify(expr, evaluate=False)
        sym     = sympify(expr)

        # ── GUARD 3: sympify zwróciło nie-wyrażenie (tuple, list, set) ───────
        if isinstance(sym, (tuple, list, set, frozenset)):
            return ParsedExpr(
                raw=expr,
                error=f"not a mathematical expression: sympify returned {type(sym).__name__}"
            )

        trig_fns = sum(1 for fn in ("sin", "cos", "tan") if fn in expr)

        return ParsedExpr(
            raw          = expr,
            sym          = sym,
            sym_raw      = sym_raw,
            is_zoo       = (sym == zoo),
            is_const     = bool(sym.is_number and sym not in (oo, -oo, zoo, nan)),
            has_division = ("/" in expr or "**-1" in expr),
            cycles       = expr.count("(") + expr.count(")"),
            fractions    = expr.count("/"),
            powers       = len(re.findall(r"\*\*", expr)),
            has_trig     = trig_fns > 0,
            trig_count   = trig_fns,
            has_pi       = "pi" in expr,
        )

    except Exception as e:
        return ParsedExpr(raw=expr, error=str(e))
