# ============================================
# PARADOX TRIGGER MODULE FOR MATH-VALIDATOR
# ============================================
#
# Kanoniczna implementacja (patrz math_validator_triggers.py — tamten plik
# jest teraz cienkim re-eksportem nad tym modułem, nie osobną kopią).
# Wpięty do pipeline_v3.validate_all() jako opcjonalny parametr `steps`:
# gdy podany, analizuje dostarczoną sekwencję kroków derywacji pod kątem
# czterech paradoksów (P_SCALE/P_STRUCTURE/P_ASSUMPTION/P_CONTINUITY).
# Nieużywany, gdy `steps` nie jest podane — pojedyncze wyrażenie nie ma
# sekwencji kroków, więc nie ma tu nic do wykrycia.

from enum import Enum

class TriggerType(Enum):
    P_SCALE = "scale"
    P_STRUCTURE = "structure"
    P_ASSUMPTION = "assumption"
    P_CONTINUITY = "continuity"
    NONE = "none"

class TriggerResult:
    def __init__(self, triggered=False, trigger_type=TriggerType.NONE, location=None, message=""):
        self.triggered = triggered
        self.trigger_type = trigger_type
        self.location = location
        self.message = message

    def as_dict(self):
        return {
            "triggered": self.triggered,
            "type": self.trigger_type.value,
            "location": self.location,
            "message": self.message
        }

class ParadoxTriggerModule:
    """
    MODULE: Paradox Trigger
    Detects logical paradoxes (pęknięcia modelu) in mathematical validation.
    """

    def __init__(self):
        self.last_result = TriggerResult()

    def analyze(self, model_steps):
        """
        Main entry point for the module.
        model_steps: list of dicts describing each validation step.
        """
        self.last_result = self._detect(model_steps)
        return self.last_result

    def _detect(self, steps):
        for step_id, step in enumerate(steps):

            # --- TRIGGER P-SCALE ---
            if step.get("local_valid") and not step.get("global_valid"):
                return TriggerResult(
                    True,
                    TriggerType.P_SCALE,
                    step_id,
                    "Local model works, global model breaks (scale paradox)."
                )

            # --- TRIGGER P-STRUCTURE ---
            if step.get("definition_changes_sense"):
                return TriggerResult(
                    True,
                    TriggerType.P_STRUCTURE,
                    step_id,
                    "Definition changes meaning across regimes (structure paradox)."
                )

            # --- TRIGGER P-ASSUMPTION ---
            if step.get("assumptions_conflict"):
                return TriggerResult(
                    True,
                    TriggerType.P_ASSUMPTION,
                    step_id,
                    "Assumptions are individually valid but contradictory together."
                )

            # --- TRIGGER P-CONTINUITY ---
            if step.get("logical_jump_detected"):
                return TriggerResult(
                    True,
                    TriggerType.P_CONTINUITY,
                    step_id,
                    "Logical continuity breaks at this step (continuity paradox)."
                )

        return TriggerResult(False, TriggerType.NONE, None, "No paradox detected.")

    def get_last(self):
        """Returns last trigger result."""
        return self.last_result
