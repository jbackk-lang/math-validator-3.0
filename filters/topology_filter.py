"""
filters/topology_filter.py — filtr topologiczny (domena ciągłości)

Poprawki v2:
  - Używa p.sym_raw (NIEzewaluowane) zamiast p.sym do obliczenia domeny.
    Dzięki temu x/x → domena ℝ\{0} zamiast ℝ (oryginał dostawał już
    uproszczone sym=1 i zwracał Reals, gubiąc osobliwość w x=0).
  - Poprawna ścieżka importu: sympy.calculus.util.continuous_domain
    (oryginał importował z sympy bezpośrednio — błąd w sympy 1.12+)
  - Fallback do sym gdy sym_raw jest None
"""

from core import ParsedExpr
from sympy import symbols, S
from sympy.calculus.util import continuous_domain

x = symbols("x")


def run(p: ParsedExpr) -> dict:
    if not p.ok:
        return {"ok": False, "error": p.error}

    # ── POPRAWKA: analiza domeny na NIEzewaluowanym wyrażeniu ─────────────────
    # p.sym_raw = sympify(expr, evaluate=False) zachowuje strukturę x/x
    # p.sym     = sympify(expr)                 upraszcza x/x → 1
    expr_for_domain = p.sym_raw if p.sym_raw is not None else p.sym

    try:
        domain      = continuous_domain(expr_for_domain, x, S.Reals)
        is_all_reals = (domain == S.Reals)
        return {
            "domain":       str(domain),
            "is_all_reals": is_all_reals,
            "ok":           True,
        }
    except Exception as ex:
        # Fallback: jeśli sym_raw nie daje się przetworzyć, spróbuj sym
        try:
            domain      = continuous_domain(p.sym, x, S.Reals)
            is_all_reals = (domain == S.Reals)
            return {
                "domain":       str(domain),
                "is_all_reals": is_all_reals,
                "ok":           True,
                "note":         "domain computed from evaluated expression (sym_raw failed)",
            }
        except Exception as ex2:
            return {"ok": False, "domain": "unknown", "error": str(ex2)}
