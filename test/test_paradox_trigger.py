"""
test_paradox_trigger.py — testy dla wpięcia modułu paradoksów do walidatora.

Kontekst: math_validator_triggers.py i paradox_trigger_module.py były
niezależnymi kopiami tej samej logiki (ten sam TriggerType, ta sama
sekwencja 4 warunków P_SCALE/P_STRUCTURE/P_ASSUMPTION/P_CONTINUITY, jedna
jako wolna funkcja, druga jako klasa) — żaden z nich nie był importowany
przez pipeline_v3.py. Naprawione tak jak §6 timdr-signal-framework
przewiduje: paradox_trigger_module.py jest teraz jedynym miejscem, gdzie
żyje logika; math_validator_triggers.py jest cienkim re-eksportem.
Te testy pilnują: (1) duplikacja nie wróci po cichu (test tożsamości
obiektu, nie tylko równości wyniku); (2) moduł jest realnie wpięty do
pipeline_v3.validate_all() przez opcjonalny parametr `steps`; (3) bez
`steps` zachowanie jest identyczne jak przed zmianą (brak klucza
"paradox", status niezmieniony).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math_validator_triggers as mvt
import paradox_trigger_module as ptm
from pipeline_v3 import validate_all


def test_deduplikacja_tozsamosc_klasy():
    # Nie tylko "te same pola" — dokładnie ten SAM obiekt klasy, żeby
    # przyszła edycja jednego pliku nie mogła po cichu odejść od drugiego.
    assert mvt.ParadoxTriggerModule is ptm.ParadoxTriggerModule
    assert mvt.TriggerType is ptm.TriggerType
    assert mvt.TriggerResult is ptm.TriggerResult


def test_detect_triggers_deleguje_a_nie_duplikuje():
    steps = [{"local_valid": True, "global_valid": False}]
    stary_interfejs = mvt.detect_triggers(steps)
    nowy_interfejs = ptm.ParadoxTriggerModule().analyze(steps)
    assert stary_interfejs.triggered == nowy_interfejs.triggered
    assert stary_interfejs.trigger_type == nowy_interfejs.trigger_type
    assert stary_interfejs.trigger_type is ptm.TriggerType.P_SCALE


def test_validate_all_bez_steps_nie_dodaje_paradox():
    # Zachowanie bez `steps` musi być identyczne jak przed integracją.
    result = validate_all("2*x + 3*x")
    assert "paradox" not in result


def test_validate_all_z_steps_wykrywa_paradoks_skali():
    result = validate_all(
        "2*x + 3*x",
        steps=[{"local_valid": True, "global_valid": False}],
    )
    assert "paradox" in result
    assert result["paradox"]["triggered"] is True
    assert result["paradox"]["type"] == "scale"
    # Wykryty paradoks musi wpływać na ogólny status pipeline'u.
    assert result["status"] == "issues_found"


def test_validate_all_z_steps_bez_paradoksu():
    result = validate_all(
        "2*x + 3*x",
        steps=[{"local_valid": True, "global_valid": True}],
    )
    assert result["paradox"]["triggered"] is False
    assert result["paradox"]["type"] == "none"
