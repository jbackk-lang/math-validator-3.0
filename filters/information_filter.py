"""
information_filter.py — operator ι (informacja)
Analiza informacyjna wyrażenia:
- entropia symboli
- redundancja
- złożoność strukturalna
- gęstość operatorów
- stabilność informacyjna

Zgodne z modelem Λ–τ–ρ–ι.
"""

from core import ParsedExpr
import math
import re


def _entropy(text: str) -> float:
    """Shannon-like entropy of characters."""
    if not text:
        return 0.0
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    total = len(text)
    return -sum((c/total) * math.log2(c/total) for c in freq.values())


def _redundancy(text: str, H: float) -> float:
    """Redundancy = 1 - H/Hmax."""
    if not text:
        return 0.0
    Hmax = math.log2(len(set(text)))
    if Hmax == 0:
        return 0.0
    return max(0.0, 1 - H/Hmax)


def _complexity_score(symbols: int, operators: int, entropy: float) -> float:
    """Prosty wskaźnik złożoności."""
    if symbols == 0:
        return 0.0
    return min(1.0, (operators / symbols) * 0.5 + entropy * 0.1)


def run(p: ParsedExpr) -> dict:
    if p.error:
        return {
            "status": "error",
            "message": p.error,
            "notes": ["information_filter: błąd parse()"]
        }

    expr = p.raw.strip()
    if not expr:
        return {
            "status": "skip",
            "message": "puste wyrażenie",
            "notes": []
        }

    # liczenie symboli i operatorów
    symbols = len(expr)
    operators = len(re.findall(r"[+\-*/^=()]", expr))

    # entropia
    H = _entropy(expr)
    R = _redundancy(expr, H)
    C = _complexity_score(symbols, operators, H)

    # stabilność informacyjna
    if C < 0.25:
        stability = "very_low"
    elif C < 0.45:
        stability = "low"
    elif C < 0.65:
        stability = "medium"
    elif C < 0.85:
        stability = "high"
    else:
        stability = "very_high"

    return {
        "status": "ok",
        "symbols": symbols,
        "operators": operators,
        "entropy": round(H, 4),
        "redundancy": round(R, 4),
        "complexity": round(C, 4),
        "stability": stability,
        "notes": [
            "operator ι — analiza informacyjna",
            "zgodne z modelem Λ–τ–ρ–ι"
        ]
    }
