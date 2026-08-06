"""
normalize.py — Normalizacja Wyrażeń (v3)

Upraszcza wyrażenia symbolicznie (2*x + 3*x -> 5*x, x/x -> 1 dla x≠0, itd.)
i jawnie raportuje utracone założenia o dziedzinie, żeby normalizacja nie
"ukrywała" osobliwości (nawiązanie do filters/misleading_filter.py z v2).

Użycie:
    from normalize import normalize_expression
    normalize_expression("2*x + 3*x")
    normalize_expression("x/x")
"""
from __future__ import annotations

from typing import Optional

from sympy import (
    sympify, simplify, expand, factor, together, cancel, nsimplify,
    trigsimp, powsimp, radsimp, S, Symbol,
)
from sympy.calculus.util import continuous_domain


def normalize_expression(expr_str: str, symbol: str = "x", methods: Optional[list[str]] = None) -> dict:
    """
    methods: podzbiór ["simplify","expand","factor","together","cancel",
                       "trigsimp","powsimp","radsimp"], domyślnie wszystkie
             sensowne w kolejności heurystycznej.
    """
    try:
        raw = sympify(expr_str, evaluate=False)
        original = sympify(expr_str)
    except Exception as e:
        return {"status": "error", "message": f"błąd parsowania: {e}"}

    x = Symbol(symbol)
    has_division = ("/" in expr_str) or original.has(S.ComplexInfinity)

    steps = []
    current = original
    method_list = methods or ["cancel", "together", "trigsimp", "simplify"]
    fn_table = {
        "simplify": simplify, "expand": expand, "factor": factor,
        "together": together, "cancel": cancel, "trigsimp": trigsimp,
        "powsimp": powsimp, "radsimp": radsimp,
    }
    for name in method_list:
        fn = fn_table.get(name)
        if fn is None:
            continue
        try:
            new = fn(current)
        except Exception:
            continue
        if new != current:
            steps.append({"method": name, "before": str(current), "after": str(new)})
            current = new

    simplified = current
    caveats = []

    # Sprawdzenie, czy normalizacja "zgubiła" osobliwość (np. x/x -> 1)
    if has_division and original.free_symbols:
        try:
            dom_before = continuous_domain(raw, x, S.Reals)
            dom_after = continuous_domain(simplified, x, S.Reals)
            if dom_before != dom_after:
                caveats.append(
                    f"Uwaga: uproszczone wyrażenie ma inną dziedzinę ciągłości "
                    f"({dom_after}) niż oryginał ({dom_before}). "
                    f"Poprawny zapis: {simplified} dla x ∈ {dom_before}."
                )
        except Exception:
            pass

    return {
        "status": "ok",
        "original": str(original),
        "normalized": str(simplified),
        "changed": str(original) != str(simplified),
        "steps": steps,
        "caveats": caveats,
    }
