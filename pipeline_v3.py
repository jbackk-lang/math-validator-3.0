"""
pipeline_v3.py — Zunifikowany potok walidacji math-validator v3.

Łączy filtry z v2 (syntax, algebra, logic, misleading) z nowymi
modułami v3 (symbolic_logic, units, normalize, variables, ambiguity,
linalg, rich errors) oraz wtyczkami z plugins.py — w jedno wywołanie.

Użycie:
    from pipeline_v3 import validate_all
    validate_all("2*x + 3*x")
    validate_all("(A ∧ B) → C", formula=True)
    validate_all("v*t", units={"v": "m/s", "t": "s"})
    validate_all("Matrix([[1,2]]) * Matrix([[1,2]])", matrix=True)
"""
from __future__ import annotations

from typing import Optional

from core import parse
from filters import (
    syntax_filter, algebra_filter, logic_filter, misleading_filter,
    harmonic_filter, information_filter, numeric_filter, prime_spectrum_filter,
    millennium_filter, moebius_filter, singularity_filter, topology_filter,
)
from filters.symbolic_logic_filter import run_formula
from units import analyze_units
from normalize import normalize_expression
from variables import analyze_variables
from ambiguity import find_ambiguities, PrecedenceConfig
from linalg import validate_matrix_expression
from errors import diagnose_syntax
import plugins


def validate_all(
    expr: str,
    *,
    formula: bool = False,
    units: Optional[dict] = None,
    matrix: bool = False,
    precedence_config: Optional[PrecedenceConfig] = None,
    run_plugins: bool = True,
) -> dict:
    result: dict = {"expression": expr}

    # ── Ścieżka: formuła logiki zdaniowej ────────────────────────────────
    if formula:
        result["symbolic_logic"] = run_formula(expr)
        return result

    # ── Ścieżka: wyrażenie macierzowe ────────────────────────────────────
    if matrix:
        result["linear_algebra"] = validate_matrix_expression(expr)
        return result

    # ── Diagnostyka składniowa (przed sympify, żeby złapać literówki itp.) ──
    result["syntax_diagnostics"] = diagnose_syntax(expr)

    # ── Parsowanie rdzeniowe (core.py z v2) ──────────────────────────────
    parsed = parse(expr)
    result["parsed_ok"] = parsed.ok
    if parsed.error:
        result["parse_error"] = parsed.error

    # ── Filtry v2 ─────────────────────────────────────────────────────────
    result["syntax"] = syntax_filter.run(parsed)
    if parsed.ok:
        result["algebra"] = algebra_filter.run(parsed)
        result["logic"] = logic_filter.run(parsed)
        result["misleading"] = misleading_filter.run(parsed)
        result["harmonic"] = harmonic_filter.run(parsed)
        result["information"] = information_filter.run(parsed)
        result["numeric"] = numeric_filter.run(parsed)
        result["prime_spectrum"] = prime_spectrum_filter.run(parsed)
        # POPRAWKA: te 4 filtry istniały w v2.0 ale zniknęły w v3.0 (nie
        # skopiowano ich przy migracji) - użytkownik poprosił, by kolejne
        # wersje zawierały w sobie poprzednie (superset), więc przywrócono.
        result["millennium"] = millennium_filter.run(parsed)
        result["moebius"] = moebius_filter.run(parsed)
        result["singularity"] = singularity_filter.run(parsed)
        result["topology"] = topology_filter.run(parsed)

        # ── Moduły v3 ──────────────────────────────────────────────────
        result["normalize"] = normalize_expression(expr)
        result["variables"] = analyze_variables(expr)
        result["ambiguity"] = find_ambiguities(expr, precedence_config or PrecedenceConfig())

        if units:
            result["units"] = analyze_units(expr, units)

    # ── Wtyczki zewnętrzne ────────────────────────────────────────────────
    if run_plugins:
        registered = plugins.get_filters()
        if registered:
            result["plugins"] = plugins.run_all_plugins(parsed)

    overall_ok = (
        parsed.ok
        and result["syntax"].get("ok", True)
        and result.get("algebra", {}).get("status") != "error"
        and not result["syntax_diagnostics"]["diagnostics"]
    )
    result["status"] = "ok" if overall_ok else "issues_found"
    return result
