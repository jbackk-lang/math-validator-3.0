"""
prime_spectrum_filter.py — analizuje widmo liczb pierwszych
związane z wyrażeniem typu N (liczba naturalna).

Idea:
- jeśli wyrażenie upraszcza się do liczby całkowitej N > 2
- bierzemy liczby pierwsze p ≤ N**(1/3)
- liczymy:
  - listę pierwszych
  - różnice między kolejnymi (gaps)
  - stosunki p_{n+1} / p_n
  - prostą klasyfikację widma (quasi 1/f vs „płaskie”)
"""

from core import ParsedExpr
from sympy import primerange
from math import log


def _classify_spectrum(gaps):
    """
    Bardzo prosta heurystyka:
    - jeśli gaps rosną mniej więcej logarytmicznie → 'log_spiral_1_over_f'
    - inaczej → 'irregular'
    """
    if len(gaps) < 3:
        return "too_few_primes"

    xs = list(range(1, len(gaps) + 1))
    logs = [log(x + 1) for x in xs]

    def norm(vs):
        vmin, vmax = min(vs), max(vs)
        if vmax == vmin:
            return [0.0 for _ in vs]
        return [(v - vmin) / (vmax - vmin) for v in vs]

    g_n = norm(gaps)
    l_n = norm(logs)

    diff = sum(abs(a - b) for a, b in zip(g_n, l_n)) / len(g_n)

    if diff < 0.25:
        return "log_spiral_1_over_f"
    return "irregular"


def run(p: ParsedExpr) -> dict:
    if p.error:
        return {
            "status": "error",
            "message": p.error,
            "notes": ["nie można przeanalizować widma liczb pierwszych — błąd parse()"]
        }

    if not (p.sym is not None and p.sym.is_integer):
        return {
            "status": "skip",
            "message": "wyrażenie nie jest liczbą całkowitą — pomijam prime_spectrum",
            "notes": []
        }

    try:
        N = int(p.sym)
    except Exception:
        return {
            "status": "error",
            "message": f"nie można zrzutować {p.sym} na int",
            "notes": []
        }

    if N <= 2:
        return {
            "status": "skip",
            "message": "N ≤ 2 — brak sensownego widma liczb pierwszych",
            "notes": []
        }

    N_third = int(round(N ** (1/3)))
    if N_third < 3:
        N_third = 3

    primes = list(primerange(2, N_third + 1))

    if len(primes) < 2:
        return {
            "status": "ok",
            "prime_count": len(primes),
            "primes": primes,
            "gaps": [],
            "ratios": [],
            "spectrum_type": "too_few_primes",
            "notes": ["za mało liczb pierwszych w zakresie N^(1/3)"]
        }

    gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]
    ratios = [primes[i+1] / primes[i] for i in range(len(primes) - 1)]

    spectrum_type = _classify_spectrum(gaps)

    notes = [
        f"N = {N}",
        f"zakres pierwszych: do N^(1/3) ≈ {N_third}",
        f"liczba pierwszych w zakresie: {len(primes)}",
    ]
    if spectrum_type == "log_spiral_1_over_f":
        notes.append("widmo zgodne z logarytmiczną spiralą / 1/f (Λ–τ–ρ/TIMDR)")

    return {
        "status": "ok",
        "prime_count": len(primes),
        "primes": primes,
        "gaps": gaps,
        "ratios": ratios,
        "spectrum_type": spectrum_type,
        "notes": notes,
    }
