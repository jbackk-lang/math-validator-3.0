"""
variables.py — Analiza Zależności (zmienne wolne vs związane) — v3

Identyfikuje zmienne w wyrażeniu i określa, czy są wolne czy związane
(np. przez Sum, Integral, Derivative, Limit, Product). Przydatne przy
definiowaniu funkcji — mówi, od czego wyrażenie *faktycznie* zależy.

Użycie:
    from variables import analyze_variables
    analyze_variables("Integral(x*y, (x, 0, 1))")
    -> free: {y}, bound: {x (w Integral)}
"""
from __future__ import annotations

from sympy import sympify, Symbol
from sympy.concrete.expr_with_limits import ExprWithLimits
from sympy.core.function import Derivative
from sympy.series.limits import Limit


_BINDER_NAMES = {"Sum", "Integral", "Product", "Derivative", "Limit"}


def _walk_binders(expr, bound_info: list):
    """Zbiera informacje o zmiennych związanych w każdym napotkanym binderze."""
    func_name = getattr(expr.func, "__name__", "")

    if isinstance(expr, (ExprWithLimits, Derivative)) or func_name in _BINDER_NAMES:
        bound_vars = set()
        if isinstance(expr, ExprWithLimits):
            for lim in expr.limits:
                bound_vars.add(lim[0])
        elif isinstance(expr, Derivative):
            for var, _count in expr.variable_count:
                bound_vars.add(var)
        if bound_vars:
            bound_info.append({
                "binder": func_name,
                "bound_variables": sorted(str(v) for v in bound_vars),
                "expression": str(expr),
            })

    for arg in getattr(expr, "args", ()):
        _walk_binders(arg, bound_info)


def analyze_variables(expr_str: str) -> dict:
    try:
        expr = sympify(expr_str)
    except Exception as e:
        return {"status": "error", "message": f"błąd parsowania: {e}"}

    free_vars = sorted(str(s) for s in expr.free_symbols)

    bound_info: list = []
    _walk_binders(expr, bound_info)

    all_bound_names = set()
    for b in bound_info:
        all_bound_names.update(b["bound_variables"])

    shadowed = sorted(set(free_vars) & all_bound_names)

    notes = []
    if shadowed:
        notes.append(
            f"Uwaga: zmienne {shadowed} występują zarówno jako wolne, jak i związane "
            f"w innym zakresie wyrażenia (możliwe przesłonięcie / shadowing)."
        )

    return {
        "status": "ok",
        "expression": str(expr),
        "free_variables": free_vars,
        "bound_variables": bound_info,
        "shadowed_variables": shadowed,
        "depends_only_on": free_vars,
        "notes": notes,
    }
