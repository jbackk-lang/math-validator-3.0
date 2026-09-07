"""
test_api_paradox.py — testy endpointu API eksponujacego
paradox_trigger_module.py bezposrednio (a nie tylko jako opcjonalny klucz
'paradox' w pelnej odpowiedzi /api/v3/validate, gdy caller poda `steps`).

Kontekst: moduł byl wpiety do pipeline_v3.validate_all() (patrz
test/test_paradox_trigger.py), ale ani API, ani WebGUI (index.html) go nie
eksponowaly - w praktyce niewidoczny/niesuzytkowalny bez czytania kodu
pipeline'u. Ten plik testuje naprawe tego samego problemu, ktory README
juz dokumentuje dla millennium_filter (patrz test_api_millennium.py).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_paradox_wykrywa_paradoks_skali():
    r = client.post("/api/v3/paradox", json={
        "steps": [{"local_valid": True, "global_valid": False}]
    })
    assert r.status_code == 200
    data = r.json()
    assert data["triggered"] is True
    assert data["type"] == "scale"


def test_paradox_brak_paradoksu():
    r = client.post("/api/v3/paradox", json={
        "steps": [{"local_valid": True, "global_valid": True}]
    })
    assert r.status_code == 200
    data = r.json()
    assert data["triggered"] is False
    assert data["type"] == "none"


def test_paradox_wykrywa_paradoks_struktury():
    r = client.post("/api/v3/paradox", json={
        "steps": [{"definition_changes_sense": True}]
    })
    assert r.status_code == 200
    assert r.json()["type"] == "structure"


def test_paradox_pusta_lista_krokow_zwraca_brak_paradoksu():
    r = client.post("/api/v3/paradox", json={"steps": []})
    assert r.status_code == 200
    assert r.json()["triggered"] is False


def test_paradox_dostepny_takze_przez_pelna_walidacje():
    """Regresja: /api/v3/validate powinien zawierac klucz 'paradox', gdy
    caller poda `steps` (dedykowany endpoint uzupelnia, nie zastepuje)."""
    r = client.post("/api/v3/validate", json={
        "expression": "2*x + 3*x",
        "steps": [{"local_valid": True, "global_valid": False}],
    })
    assert r.status_code == 200
    data = r.json()
    assert "paradox" in data
    assert data["paradox"]["triggered"] is True
    assert data["status"] == "issues_found"


def test_paradox_nieobecny_gdy_steps_nie_podano():
    """Regresja: bez `steps` /api/v3/validate zachowuje sie jak przed
    integracja modulu paradoksow."""
    r = client.post("/api/v3/validate", json={"expression": "2*x + 3*x"})
    assert r.status_code == 200
    assert "paradox" not in r.json()
