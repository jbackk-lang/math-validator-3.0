"""
filters/misleading_filter.py — wykrywa wyrażenia mylące

Poprawki v2:
  - Nowy przypadek: x/x → upraszcza do 1 ale ma osobliwość (ukryta domena)
    Porównuje sym (zewaluowane) z sym_raw (nieewaluowane): jeśli różne
    i oryginał miał dzielenie → misleading
  - Nowy przypadek: wyrażenia z has_division gdzie domena sym_raw ≠ Reals
    ale sym daje Reals (zgubiona osobliwość po uproszczeniu)
"""

from core import ParsedExpr
from sympy import symbols, simplify, cancel, S
from sympy.calculus.util import continuous_domain

x = symbols("x")


def run(p: ParsedExpr) -> dict:
    if not p.ok:
        return {"ok": False, "error": p.error}

    issues = []

    try:
        s = simplify(p.sym)

        # ── Przypadek 1: upraszcza do 0 ale ma dzielnik ──────────────────────
        if str(s) == "0" and p.has_division:
            issues.append(
                "misleading_zero: wyrażenie upraszcza się do 0, "
                "ale dzielnik może być 0 dla pewnych x"
            )

        # ── Przypadek 2: upraszczalne ułamki (cancel) ─────────────────────────
        try:
            c = cancel(p.sym)
            if str(c) != str(p.sym) and p.has_division:
                issues.append(f"simplifiable_fraction: {p.sym} → {c}")
        except Exception:
            pass

        # ── POPRAWKA: x/x i podobne — zgubiona osobliwość ────────────────────
        # sym_raw ≠ sym AND has_division → sprawdź czy domena się różni
        if p.sym_raw is not None and p.has_division:
            try:
                domain_raw = continuous_domain(p.sym_raw, x, S.Reals)
                domain_sym = continuous_domain(p.sym,     x, S.Reals)
                if domain_raw != domain_sym:
                    issues.append(
                        f"hidden_singularity: po uproszczeniu domena wygląda jak "
                        f"{domain_sym}, ale oryginalne wyrażenie ma domenę {domain_raw}"
                    )
            except Exception:
                pass

    except Exception:
        pass

    return {
        "misleading_issues": issues,
        "count":             len(issues),
        "ok":                True,
    }
