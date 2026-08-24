"""
test_api_millennium.py — testy nowych endpointow API eksponujacych
filters/millennium_filter.py bezposrednio (a nie tylko jako jeden z ~15
kluczy pogrzebanych w pelnej odpowiedzi /api/v3/validate).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_millennium_wykrywa_riemanna():
    r = client.post("/api/v3/millennium", json={"expression": "zeta(1/2 + I*t)"})
    assert r.status_code == 200
    data = r.json()
    assert data["triggered"] is True
    names = [m["name"] for m in data["matches"]]
    assert "Hipoteza Riemanna" in names


def test_millennium_brak_powiazan():
    r = client.post("/api/v3/millennium", json={"expression": "x + 1"})
    assert r.status_code == 200
    assert r.json()["triggered"] is False


def test_millennium_dziala_nawet_gdy_wyrazenie_sie_nie_parsuje():
    """Detekcja slow kluczowych dziala na surowym tekscie, wiec powinna
    wykryc np. 'NP-complete' nawet jesli sympify() by sie na tym wywalilo."""
    r = client.post("/api/v3/millennium", json={"expression": "problem NP-complete w grafie"})
    assert r.status_code == 200
    data = r.json()
    assert data["triggered"] is True
    ids = [m["problem_id"] for m in data["matches"]]
    assert "MP-1" in ids


def test_millennium_katalog_zwraca_wszystkie_7_problemow():
    r = client.get("/api/v3/millennium/problems")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 7
    assert len(data["problems"]) == 7
    keys = {p["key"] for p in data["problems"]}
    assert keys == {
        "P_vs_NP", "Riemann", "Birch_Swinnerton_Dyer", "Yang_Mills",
        "Navier_Stokes", "Poincare", "Hodge",
    }
    # katalog nie powinien ujawniac surowych regexow keywords - to szczegol
    # implementacyjny filtra, nie cos co powinno trafic do publicznego API
    assert all("keywords" not in p for p in data["problems"])


def test_millennium_katalog_oznacza_status_problemow():
    r = client.get("/api/v3/millennium/problems")
    statuses = {p["key"]: p["status"] for p in r.json()["problems"]}
    assert statuses["Poincare"] == "SOLVED"
    assert statuses["Riemann"] == "OPEN"


def test_millennium_jest_tez_w_pelnej_walidacji():
    """Regresja: /api/v3/validate nadal powinien zawierac klucz 'millennium'
    (dedykowany endpoint go uzupelnia, a nie zastepuje)."""
    r = client.post("/api/v3/validate", json={"expression": "zeta(s)"})
    assert r.status_code == 200
    assert "millennium" in r.json()
