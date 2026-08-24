"""
numeric_filter.py — rozwiązuje wyrażenie numerycznie i klasyfikuje rozwiązania.
Używa sym z ParsedExpr — nie wywołuje sympify().
"""
from core import ParsedExpr
from sympy import solve, I, re as sym_re, im as sym_im


def run(p: ParsedExpr) -> dict:
    if p.error or p.sym is None:
        return {"status": "error", "solutions": [], "notes": [p.error]}

    notes = []
    try:
        sols = solve(p.sym, p.x)

        real_sols    = []
        complex_sols = []

        for s in sols:
            try:
                if sym_im(s) == 0:
                    real_sols.append(str(s))
                else:
                    complex_sols.append(str(s))
            except Exception:
                real_sols.append(str(s))

        if complex_sols:
            notes.append(f"rozwiązania zespolone: {complex_sols}")

        if not sols:
            notes.append("brak rozwiązań rzeczywistych")

        return {
            "status": "ok",
            "solutions": real_sols,
            "complex_solutions": complex_sols,
            "count": len(sols),
            "notes": notes
        }

    except Exception as e:
        return {
            "status": "error",
            "solutions": [],
            "complex_solutions": [],
            "count": 0,
            "notes": [str(e)]
        }
