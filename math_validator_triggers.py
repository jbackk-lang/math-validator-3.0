"""
math_validator_triggers.py — cienki re-export ponad paradox_trigger_module.py.

POPRAWKA (duplication-drift, wzorzec z §6 timdr-signal-framework): ten plik
kiedyś zawierał NIEZALEŻNĄ drugą kopię tej samej logiki (TriggerType,
TriggerResult, 4 warunki P_SCALE/P_STRUCTURE/P_ASSUMPTION/P_CONTINUITY) co
paradox_trigger_module.py — dwie kopie tej samej rzeczy, jedna jako wolna
funkcja, druga jako klasa, utrzymywane osobno i grożące rozjechaniem się przy
pierwszej poprawce w jednej z nich. Naprawione przez sprowadzenie tego pliku
do re-eksportu: paradox_trigger_module.py jest teraz jedynym miejscem, gdzie
faktycznie żyje logika detekcji. detect_triggers() zachowany dla wstecznej
kompatybilności (stary interfejs funkcyjny), ale deleguje do
ParadoxTriggerModule zamiast duplikować jej ciało.

Patrz test/test_paradox_trigger.py — test tożsamości obiektu
(assertIs), nie tylko równości wyniku, żeby ta duplikacja nie mogła po cichu
wrócić.
"""
from paradox_trigger_module import TriggerType, TriggerResult, ParadoxTriggerModule


def detect_triggers(model_steps) -> TriggerResult:
    """
    model_steps: lista kroków walidacji (każdy krok to obiekt lub dict).
    Zachowany dla wstecznej kompatybilności ze starym interfejsem funkcyjnym —
    deleguje do ParadoxTriggerModule, nie duplikuje jej logiki.
    """
    return ParadoxTriggerModule().analyze(model_steps)
