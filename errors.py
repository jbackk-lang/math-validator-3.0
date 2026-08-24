"""
errors.py — Bogatsze Komunikaty Błędów (v3)

Zamiast "błąd składni" zwraca dokładną pozycję, fragment z karetką
(^) wskazującą miejsce błędu, oraz sugerowaną poprawkę — np.:

    Błąd w pozycji 5: brakujący nawias zamykający po 'sin('

Działa niezależnie od reszty projektu (operuje na surowym stringu +
opcjonalnie na wyjątku sympy), więc może być wywołany zarówno przed,
jak i po core.parse().
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Optional

KNOWN_FUNCTIONS = [
    "sin", "cos", "tan", "cot", "sec", "csc",
    "asin", "acos", "atan", "acot",
    "sinh", "cosh", "tanh",
    "exp", "log", "ln", "sqrt", "root", "Abs",
    "factorial", "gamma", "binomial",
    "Sum", "Integral", "Derivative", "Limit", "Product", "Matrix",
]
KNOWN_CONSTANTS = ["pi", "E", "I", "oo", "zoo", "nan"]


@dataclass
class Diagnostic:
    code: str
    message: str
    position: int
    hint: Optional[str] = None

    def render(self, source: str) -> str:
        pointer = " " * self.position + "^"
        lines = [f"Błąd w pozycji {self.position}: {self.message}"]
        lines.append(source)
        lines.append(pointer)
        if self.hint:
            lines.append(f"Podpowiedź: {self.hint}")
        return "\n".join(lines)


def _check_parens(expr: str) -> list[Diagnostic]:
    diags = []
    stack = []
    for i, ch in enumerate(expr):
        if ch == "(":
            stack.append(i)
        elif ch == ")":
            if not stack:
                diags.append(Diagnostic(
                    "unmatched_closing_paren",
                    "nadmiarowy nawias zamykający ')' bez odpowiadającego '('",
                    i,
                    hint="usuń ten nawias lub dodaj brakujący '(' wcześniej w wyrażeniu",
                ))
            else:
                stack.pop()
    for pos in stack:
        # spróbuj rozpoznać, czy to wywołanie znanej funkcji
        before = expr[max(0, pos - 12):pos]
        func_match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", before)
        func_name = func_match.group(1) if func_match else None
        if func_name:
            hint = f"brakujący nawias zamykający po '{func_name}('"
        else:
            hint = "brakujący nawias zamykający ')'"
        diags.append(Diagnostic("unmatched_opening_paren", hint, pos, hint=hint))
    return diags


def _check_unknown_functions(expr: str) -> list[Diagnostic]:
    diags = []
    known_lower = {f.lower(): f for f in KNOWN_FUNCTIONS}
    for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", expr):
        name = m.group(1)
        if name in KNOWN_FUNCTIONS or name in KNOWN_CONSTANTS:
            continue
        if len(name) == 1:
            continue  # prawdopodobnie zmienna użyta jako np. f(x) — nie zgadujemy
        close = difflib.get_close_matches(name.lower(), known_lower.keys(), n=1, cutoff=0.6)
        if close:
            suggestion = known_lower[close[0]]
            diags.append(Diagnostic(
                "unknown_function",
                f"nieznana funkcja {name!r}",
                m.start(1),
                hint=f"czy chodziło o '{suggestion}'?",
            ))
    return diags


def _check_double_operators(expr: str) -> list[Diagnostic]:
    diags = []
    no_pow = expr.replace("**", "\0\0")
    for m in re.finditer(r"[+\-*/]{2,}", no_pow):
        diags.append(Diagnostic(
            "double_operator",
            f"powtórzone operatory: {m.group(0)!r}",
            m.start(),
            hint="usuń nadmiarowy operator lub dodaj nawias, jeśli to zamierzone (np. 'a * (-b)')",
        ))
    return diags


def _check_trailing_leading(expr: str) -> list[Diagnostic]:
    diags = []
    if re.search(r"[+\-*/]\s*$", expr):
        diags.append(Diagnostic(
            "trailing_operator", "wyrażenie kończy się operatorem", len(expr.rstrip()) - 1,
            hint="usuń operator na końcu lub dodaj brakujący operand",
        ))
    m = re.match(r"^\s*[+*/]", expr)
    if m:
        diags.append(Diagnostic(
            "leading_operator", "wyrażenie zaczyna się od operatora dwuargumentowego", m.start(),
            hint="usuń operator na początku lub użyj '-' dla minusa unarnego",
        ))
    return diags


def diagnose_syntax(expr: str) -> dict:
    diags: list[Diagnostic] = []
    diags += _check_parens(expr)
    diags += _check_double_operators(expr)
    diags += _check_trailing_leading(expr)
    diags += _check_unknown_functions(expr)
    diags.sort(key=lambda d: d.position)

    return {
        "status": "error" if diags else "ok",
        "expression": expr,
        "diagnostics": [
            {"code": d.code, "message": d.message, "position": d.position, "hint": d.hint,
             "rendered": d.render(expr)}
            for d in diags
        ],
    }


def diagnose_sympy_exception(expr: str, exc: Exception) -> dict:
    """Owija surowy wyjątek sympy w spójny format, uzupełniając go
    o wynik diagnose_syntax() (heurystyki pozycyjne)."""
    heuristic = diagnose_syntax(expr)
    return {
        "status": "error",
        "expression": expr,
        "sympy_error": str(exc),
        "diagnostics": heuristic["diagnostics"],
    }
