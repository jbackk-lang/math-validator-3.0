"""
algebra_filter.py — wykrywa błędy algebraiczne: dzielenie przez zero,
wyrażenia nieokreślone, zespolone pierwiastki.
"""
from core import ParsedExpr
from sympy import zoo, im


def run(p: ParsedExpr) -> dict:
    if p.error:
        return {"status": "error", "message": p.error}

    notes = []

    # 1. Wyrażenie jest stale nieokreślone (zoo jako wynik)
    if p.is_zoo:
        return {
            "status": "error",
            "message": "dzielenie przez zero (zoo)",
            "notes": ["wyrażenie stale nieokreślone — mianownik zawsze 0"]
        }

    # 2. zoo jako podelement wyrażenia (np. x/(x-1) uproszczone częściowo)
    if p.sym is not None and p.sym.has(zoo):
        return {
            "status": "error",
            "message": "wyrażenie zawiera dzielenie przez zero",
            "notes": ["zoo wykryte jako podelement wyrażenia"]
        }

    # 3. Wartość zespolona (np. sqrt(-1), log(-5), itp.)
    if p.sym is not None and p.sym.is_number:
        try:
            if im(p.sym) != 0:
                notes.append(f"wyrażenie ma część urojoną: {p.sym}")
                return {
                    "status": "warning",
                    "message": "wartość zespolona",
                    "notes": notes
                }
        except Exception:
            pass

    # 4. Brak błędów algebraicznych
    return {
        "status": "ok",
        "message": "brak błędów algebraicznych",
        "notes": notes
    }
