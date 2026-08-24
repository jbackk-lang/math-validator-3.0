"""
filters/logic_filter.py — filtr logiczny Λ–τ–ρ

Poprawki v2:
  - Jawne sprawdzenie is_zoo z ParsedExpr (oryginał mógł pominąć zoo gdy
    filtr był wywoływany po algebra_filter który już zewaluował wyrażenie)
  - Dodane sprawdzenie nan jako osobny przypadek
"""

from core import ParsedExpr
from sympy import oo, zoo, nan


def run(p: ParsedExpr) -> dict:
    if not p.ok:
        return {"ok": False, "error": p.error}

    issues = []

    # ── POPRAWKA: jawne is_zoo z pola ParsedExpr ─────────────────────────────
    # Oryginał sprawdzał p.sym == zoo ale po evaluate=True sympy może już
    # uprościć wyrażenie do zoo — teraz mamy gwarancję przez pole is_zoo.
    if p.is_zoo:
        issues.append("complex_infinity (zoo)")

    # Nieskończoności rzeczywiste
    if p.sym == oo:
        issues.append("positive_infinity")
    if p.sym == -oo:
        issues.append("negative_infinity")

    # NaN
    if p.sym == nan or str(p.sym) == "nan":
        issues.append("nan")

    return {
        "issues":    issues,
        "is_finite": len(issues) == 0,
        "ok":        True,
    }
