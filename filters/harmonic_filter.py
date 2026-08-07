"""
harmonic_filter.py — wykrywa strukturę harmoniczną: funkcje trygonometryczne,
obecność π, periodyczność.
"""
from core import ParsedExpr
from sympy import periodicity


def run(p: ParsedExpr) -> dict:
    if p.error or p.sym is None:
        return {"status": "error", "harmonic": False}

    notes = []
    period = None

    if p.has_trig:
        try:
            period = periodicity(p.sym, p.x)
            period = str(period) if period is not None else None
        except Exception:
            period = None
        notes.append(f"funkcje trygonometryczne: {p.trig_count}")

    if p.has_pi:
        notes.append("wyrażenie zawiera π")

    return {
        "status": "ok",
        "harmonic": p.has_trig,
        "trig_count": p.trig_count,
        "has_pi": p.has_pi,
        "period": period,
        "notes": notes
    }
