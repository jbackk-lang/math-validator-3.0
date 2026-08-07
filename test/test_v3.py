"""
test_v3.py — testy jednostkowe modułów v3.
Uruchom: pytest test/test_v3.py  (z katalogu głównego projektu)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filters.symbolic_logic_filter import run_formula
from units import analyze_units
from normalize import normalize_expression
from variables import analyze_variables
from ambiguity import find_ambiguities, PrecedenceConfig
from linalg import validate_matrix_expression, check_multiplication_compatible
from errors import diagnose_syntax
from sympy_bridge import SymPyBridge
import plugins


# ── symbolic_logic_filter ────────────────────────────────────────────────
def test_tautology():
    r = run_formula("A ∨ ¬A")
    assert r["status"] == "ok"
    assert r["is_tautology"] is True


def test_contradiction():
    r = run_formula("A ∧ ¬A")
    assert r["is_contradiction"] is True


def test_modus_ponens_equivalence():
    r = run_formula("(A → B) ↔ (¬A ∨ B)")
    assert r["is_tautology"] is True


def test_formula_syntax_error_has_position():
    r = run_formula("A ∧ (B")
    assert r["status"] == "error"
    assert r["position"] >= 0


# ── units ─────────────────────────────────────────────────────────────────
def test_units_ok():
    r = analyze_units("v*t", {"v": "m/s", "t": "s"})
    assert r["status"] == "ok"
    assert r["result_dimension"] == "m"


def test_units_mismatch():
    r = analyze_units("x + t", {"x": "m", "t": "s"})
    assert r["status"] == "error"


def test_units_trig_requires_dimensionless():
    assert analyze_units("sin(theta)", {"theta": "rad"})["status"] == "ok"
    assert analyze_units("sin(x)", {"x": "m"})["status"] == "error"


# ── normalize ────────────────────────────────────────────────────────────
def test_normalize_linear_combination():
    r = normalize_expression("2*x + 3*x")
    assert r["normalized"] == "5*x"


def test_normalize_reports_domain_caveat():
    r = normalize_expression("(x**2 - 1)/(x-1)")
    assert r["caveats"], "powinien zgłosić utraconą osobliwość w x=1"


# ── variables ────────────────────────────────────────────────────────────
def test_free_vs_bound():
    r = analyze_variables("Integral(x*y, (x, 0, 1))")
    assert r["free_variables"] == ["y"]
    assert r["bound_variables"][0]["bound_variables"] == ["x"]


# ── ambiguity ────────────────────────────────────────────────────────────
def test_chained_division_flagged():
    r = find_ambiguities("a/b*c")
    assert r["ambiguity_count"] == 1
    assert r["ambiguities"][0]["kind"] == "chained_division"


def test_precedence_config_changes_resolution():
    cfg = PrecedenceConfig(implicit_mult_binds_tighter=True)
    r = find_ambiguities("1/2y", config=cfg)
    amb = [a for a in r["ambiguities"] if a["kind"] == "implicit_mult_vs_division"][0]
    assert amb["suggested_parenthesization"] == "1/(2*y)"


# ── linalg ───────────────────────────────────────────────────────────────
def test_matrix_multiplication_ok():
    r = validate_matrix_expression("Matrix([[1,2],[3,4]]) * Matrix([[1],[0]])")
    assert r["status"] == "ok"
    assert r["result_shape"] == (2, 1)


def test_matrix_multiplication_mismatch():
    r = validate_matrix_expression("Matrix([[1,2,3],[4,5,6]]) * Matrix([[1,2],[3,4]])")
    assert r["status"] == "error"


def test_check_multiplication_compatible_helper():
    assert check_multiplication_compatible((2, 3), (3, 4))["compatible"] is True
    assert check_multiplication_compatible((2, 3), (4, 4))["compatible"] is False


# ── errors ───────────────────────────────────────────────────────────────
def test_missing_closing_paren_position():
    r = diagnose_syntax("sin(x + 1")
    assert r["status"] == "error"
    codes = [d["code"] for d in r["diagnostics"]]
    assert "unmatched_opening_paren" in codes


def test_unknown_function_suggestion():
    r = diagnose_syntax("sinn(x)")
    hint = r["diagnostics"][0]["hint"]
    assert "sin" in hint


# ── sympy_bridge ─────────────────────────────────────────────────────────
def test_bridge_solve():
    b = SymPyBridge("x**2 - 4")
    r = b.solve("x")
    assert set(r["solutions"]) == {"-2", "2"}


# ── plugins ──────────────────────────────────────────────────────────────
def test_plugin_registration_and_run():
    if "unit_test_plugin" in plugins.get_filters():
        plugins.unregister_filter("unit_test_plugin")

    @plugins.register_filter("unit_test_plugin")
    def run(p):
        return {"status": "ok", "note": "hello from plugin"}

    results = plugins.run_all_plugins(object())
    assert results["unit_test_plugin"]["note"] == "hello from plugin"
    plugins.unregister_filter("unit_test_plugin")
