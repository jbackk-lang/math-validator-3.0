"""
singularity_filter.py — wykrywa osobliwości i skręty τ (0⁺ ≠ 0⁻).

Kluczowe naprawki względem oryginalnego repo:
1. singularities(f, x) — dodany brakujący argument symbolu
2. lru_cache na stringu (nie obiekcie SymPy) — stabilny klucz cache
3. Wykrywanie wyrażeń pre-uproszczonych do zoo przez SymPy (np. 1/(x-x))
4. Wykrywanie ukrytych osobliwości w wyrażeniach uproszczonych do stałej
5. Limity jednostronne: lim(0⁺) vs lim(0⁻) — bo +0 i -0 to nie to samo miejsce
"""
from core import ParsedExpr
from sympy import singularities, limit, oo, zoo
from functools import lru_cache


@lru_cache(maxsize=256)
def _compute(expr_str: str) -> dict:
    """Cache po surowym stringu — unikamy powtórnego sympify i singularities()."""
    from core import parse
    p = parse(expr_str)
    return _analyse(p)


def _analyse(p: ParsedExpr) -> dict:
    if p.error or p.sym is None:
        return {
            "status": "error",
            "message": p.error,
            "singularities": [],
            "ρ_defects": 0,
            "twists": 0,
            "notes": [p.error]
        }

    sing_details = []
    notes = []

    # Przypadek A: SymPy uprościł do zoo przed analizą (np. 1/(x-x))
    if p.is_zoo:
        notes.append(
            "wyrażenie stale nieokreślone (zoo) — singularność ukryta przez uproszczenie SymPy"
        )
        sing_details.append({
            "point": "symbolic",
            "lim_plus": "+∞",
            "lim_minus": "-∞",
            "twist": True,
            "note": "SymPy uprościł przed analizą (np. 1/(x-x) → zoo) — skręt τ pewny"
        })

    # Przypadek B: uproszczone do stałej, ale zawiera dzielenie → ukryta osobliwość
    elif p.is_const and p.has_division:
        notes.append(
            "wyrażenie uproszczone do stałej — możliwa ukryta osobliwość w mianowniku"
        )
        sing_details.append({
            "point": "hidden",
            "lim_plus": "?",
            "lim_minus": "?",
            "twist": False,
            "note": f"sprawdź mianownik ręcznie: {p.raw}"
        })

    # Przypadek C: standardowa analiza — singularities() z właściwym symbolem
    else:
        try:
            sings = list(singularities(p.sym, p.x))
            for s in sings:
                try:
                    lp = limit(p.sym, p.x, s, '+')
                    lm = limit(p.sym, p.x, s, '-')

                    # Skręt τ: lim(0⁺) i lim(0⁻) mają przeciwne znaki nieskończoności
                    is_twist = (
                        (lp == oo  and lm == -oo) or
                        (lp == -oo and lm == oo)
                    )

                    sing_details.append({
                        "point": str(s),
                        "lim_plus":  str(lp),
                        "lim_minus": str(lm),
                        "twist": is_twist,
                        "note": (
                            "skręt τ: 0⁺≠0⁻ — oś Möbiusa"
                            if is_twist else
                            "osobliwość bez skrętu (lim jednostronne zgodne)"
                        )
                    })

                except Exception as le:
                    sing_details.append({
                        "point": str(s),
                        "lim_plus": "?",
                        "lim_minus": "?",
                        "twist": None,
                        "note": f"błąd obliczania limitu: {le}"
                    })

        except Exception as e:
            notes.append(f"błąd singularities(): {e}")

    twists = sum(1 for s in sing_details if s.get("twist"))
    status = "twist_detected" if twists else ("ok" if not sing_details else "singularity_found")

    if twists:
        notes.append(f"{twists} skręt(ów) τ: lim(0⁺)≠lim(0⁻)")

    return {
        "status":        status,
        "singularities": sing_details,
        "ρ_defects":     len(sing_details),
        "twists":        twists,
        "notes":         notes
    }


def run(p: ParsedExpr) -> dict:
    return _compute(p.raw)
