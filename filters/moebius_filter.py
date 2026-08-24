"""
moebius_filter.py — wykrywa struktury Möbiusa: odwrócenia, pętle,
transformacje zmieniające orientację wyrażenia.

Naprawiono: usunięto zduplikowaną definicję run() — Python brał ostatnią,
pierwsza była martwym kodem.
"""
from core import ParsedExpr
import re


def run(p: ParsedExpr) -> dict:
    if p.error:
        return {"status": "error", "moebius_density": 0}

    raw = p.raw
    score = 0
    indicators = []

    # Odwrócenie przez ułamek
    if "/" in raw:
        score += 1
        indicators.append("division (/)")

    # Jawne odwrócenie **-1 (łapie też formę z nawiasem: **(-1), ** (-1) )
    # POPRAWKA: oryginalny test literału "**-1" in raw nie łapał najczęstszej
    # formy zapisu x**(-1) (z nawiasem wokół wykładnika) — inversion=False
    # dla klasycznego zapisu odwrotności, mimo że negative-power regex niżej
    # już to wykrywał. Ujednolicono na jeden wzorzec.
    _RE_INV = re.compile(r"\*\*\s*\(?\s*-\s*1\s*\)?")
    explicit_inversion = bool(_RE_INV.search(raw))
    if explicit_inversion:
        score += 2
        indicators.append("explicit inversion (**-1 / **(-1))")

    # Nawiasy — możliwe pętle lub kompozycja
    if p.cycles > 0:
        score += 1
        indicators.append(f"parentheses (cycles={p.cycles})")

    # Potęgi ujemne ogólnie (np. x**(-2))
    neg_powers = re.findall(r'\*\*\s*\(\s*-', raw)
    if neg_powers:
        score += 1
        indicators.append(f"negative powers ({len(neg_powers)}×)")

    # Poziom intensywności
    if score >= 4:
        level = "high"
    elif score >= 2:
        level = "medium"
    elif score >= 1:
        level = "low"
    else:
        level = "none"

    return {
        "status": "ok",
        "moebius_density": score,
        "level": level,
        "indicators": indicators,
        "inversion": (explicit_inversion or "/" in raw)
    }
