"""
sympy_bridge.py — Integracja z Silnikiem Symbolicznym (v3)

Po walidacji wyrażenia (składnia, algebra, logika, jednostki...) ten
moduł jest "bramą" do dalszych obliczeń w SymPy: uproszczenie,
rozwiązywanie równań, różniczkowanie, całkowanie, rozwinięcie w szereg,
eksport do LaTeX-a i ewaluacja numeryczna.

Użycie:
    from sympy_bridge import SymPyBridge
    b = SymPyBridge("x**2 - 4")
    b.solve("x")
    b.diff("x")
    b.latex()
"""
from __future__ import annotations

from typing import Optional

from sympy import (
    sympify, solve, diff, integrate, series, latex, Symbol, N, simplify, Eq,
)


class SymPyBridge:
    def __init__(self, expr_str: str):
        self.raw = expr_str
        self.error: Optional[str] = None
        try:
            self.expr = sympify(expr_str)
        except Exception as e:
            self.expr = None
            self.error = str(e)

    def _guard(self) -> Optional[dict]:
        if self.expr is None:
            return {"status": "error", "message": self.error}
        return None

    def simplify(self) -> dict:
        if (g := self._guard()) is not None:
            return g
        try:
            return {"status": "ok", "result": str(simplify(self.expr))}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def solve(self, var: str = "x") -> dict:
        if (g := self._guard()) is not None:
            return g
        try:
            sols = solve(self.expr, Symbol(var))
            return {"status": "ok", "variable": var, "solutions": [str(s) for s in sols]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def diff(self, var: str = "x", order: int = 1) -> dict:
        if (g := self._guard()) is not None:
            return g
        try:
            result = diff(self.expr, Symbol(var), order)
            return {"status": "ok", "variable": var, "order": order, "result": str(result)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def integrate(self, var: str = "x", bounds: Optional[tuple] = None) -> dict:
        if (g := self._guard()) is not None:
            return g
        try:
            x = Symbol(var)
            if bounds:
                result = integrate(self.expr, (x, bounds[0], bounds[1]))
            else:
                result = integrate(self.expr, x)
            return {"status": "ok", "variable": var, "bounds": bounds, "result": str(result)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def series(self, var: str = "x", point=0, order: int = 6) -> dict:
        if (g := self._guard()) is not None:
            return g
        try:
            result = series(self.expr, Symbol(var), point, order)
            return {"status": "ok", "result": str(result)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def evalf(self, precision: int = 15, subs: Optional[dict] = None) -> dict:
        if (g := self._guard()) is not None:
            return g
        try:
            e = self.expr.subs(subs) if subs else self.expr
            return {"status": "ok", "result": str(N(e, precision))}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def latex(self) -> dict:
        if (g := self._guard()) is not None:
            return g
        try:
            return {"status": "ok", "latex": latex(self.expr)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def solve_equation(self, other_side: str, var: str = "x") -> dict:
        """Rozwiązuje self.expr == other_side."""
        if (g := self._guard()) is not None:
            return g
        try:
            rhs = sympify(other_side)
            sols = solve(Eq(self.expr, rhs), Symbol(var))
            return {"status": "ok", "variable": var, "solutions": [str(s) for s in sols]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
