"""
test_restored_filters_v3.py — testy dla 4 filtrów przywróconych z v2.0,
które zniknęły w v3.0 przy migracji: millennium_filter, moebius_filter,
singularity_filter, topology_filter.

Użytkownik poprosił, by kolejne wersje math-validatora zawierały w sobie
poprzednie (superset) — te testy potwierdzają, że filtry są nie tylko
skopiowane jako pliki, ale realnie wpięte w pipeline_v3.validate_all()
i zwracają te same zachowania co w v2.0 (core.py jest identyczny w obu
wersjach, więc interfejs run(parsed: ParsedExpr) -> dict jest kompatybilny
1:1 — potwierdzone bezpośrednim porównaniem plików core.py).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import parse
from filters import millennium_filter, moebius_filter, singularity_filter, topology_filter
from pipeline_v3 import validate_all


# ── millennium_filter ───────────────────────────────────────────────────
def test_millennium_riemann_keyword():
    r = millennium_filter.run(parse("zeta(1/2 + I*t)"))
    assert r["triggered"] is True
    ids = [m["problem_id"] for m in r["matches"]]
    assert "MP-2" in ids


def test_millennium_no_match():
    r = millennium_filter.run(parse("x + 1"))
    assert r["triggered"] is False
    assert r["matches"] == []


# ── moebius_filter ───────────────────────────────────────────────────────
def test_moebius_basic_no_indicators():
    r = moebius_filter.run(parse("x**2 - 1"))
    assert r["status"] == "ok"
    assert r["indicators"] == []
    assert r["level"] == "none"


def test_moebius_explicit_inversion_detected():
    r = moebius_filter.run(parse("x**(-1)"))
    assert r["inversion"] is True
    assert r["moebius_density"] > 0


# ── singularity_filter ───────────────────────────────────────────────────
def test_singularity_twist_at_zero():
    r = singularity_filter.run(parse("1/x"))
    assert r["status"] == "twist_detected"
    assert r["twists"] == 1


def test_singularity_none_for_polynomial():
    r = singularity_filter.run(parse("x + 1"))
    assert r["status"] == "ok"
    assert r["ρ_defects"] == 0


# ── topology_filter ────────────────────────────────────────────────────
def test_topology_domain_with_singularity():
    r = topology_filter.run(parse("1/x"))
    assert r["ok"] is True
    assert r["is_all_reals"] is False
    assert "0" in r["domain"]


def test_topology_domain_all_reals():
    r = topology_filter.run(parse("x**2 - 4"))
    assert r["ok"] is True
    assert r["is_all_reals"] is True
    assert r["domain"] == "Reals"


# ── integracja z pipeline_v3.validate_all() ──────────────────────────────
def test_validate_all_zawiera_wszystkie_4_przywrocone_filtry():
    r = validate_all("1/x")
    for key in ("millennium", "moebius", "singularity", "topology"):
        assert key in r, f"brak klucza '{key}' w validate_all() - filtr nie jest wpiety w pipeline"
    assert r["singularity"]["status"] == "twist_detected"
    assert r["topology"]["is_all_reals"] is False
