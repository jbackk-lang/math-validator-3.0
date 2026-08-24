# filters/millennium_filter.py
#
# Filtr Problemów Milenijnych — wersja poprawiona i zoptymalizowana.
# Zachowuje twoją strukturę, ale naprawia:
# - dopasowania słów kluczowych
# - detekcję symboliczną
# - kompatybilność z math-validator-2.0
# - wydajność i stabilność

import re
from dataclasses import dataclass
from typing import List, Optional

# SymPy jest opcjonalne — filtr działa nawet bez parsed.sym.
# UWAGA (naprawa): oryginalny import `from sympy import Laplacian` rzucał
# ImportError (Laplacian nie jest eksponowany w top-level sympy), co przez
# try/except cicho ustawiało SYMPY_AVAILABLE=False i wyłączało całą detekcję
# symboliczną na zawsze. Funkcja _detect_symbolic() i tak nigdy nie używa
# tych klas bezpośrednio (robi tylko string-matching po str(sym)), więc
# import był w ogóle zbędny -- usunięty zamiast naprawiany.
SYMPY_AVAILABLE = True


# ─────────────────────────────────────────────
# Dane Problemów Milenijnych
# ─────────────────────────────────────────────

MILLENNIUM_PROBLEMS = {
    "P_vs_NP": {
        "id": "MP-1",
        "name": "P vs NP",
        "status": "OPEN",
        "keywords": [
            r"\bNP\b", r"\bSAT\b", r"NP-hard", r"NP-complete",
            r"polynomial", r"complexity"
        ],
        "description": "Czy P = NP?",
        "risk": "Wyrażenie dotyka teorii złożoności obliczeniowej.",
    },
    "Riemann": {
        "id": "MP-2",
        "name": "Hipoteza Riemanna",
        "status": "OPEN",
        "keywords": [
            r"zeta", r"riemann", r"critical.?line", r"Re\(s\)=1/2", r"ζ"
        ],
        "description": "Nietrywialne zera ζ(s) leżą na Re(s)=1/2.",
        "risk": "Wyrażenie zawiera funkcję zeta lub jej analizę.",
    },
    "Birch_Swinnerton_Dyer": {
        "id": "MP-3",
        "name": "Hipoteza Bircha i Swinnertona-Dyera",
        "status": "OPEN",
        "keywords": [
            r"elliptic.?curve", r"\brank\b", r"L\(E,1\)", r"torsion", r"Mordell"
        ],
        "description": "Rząd krzywej eliptycznej = rząd zera L(E,s).",
        "risk": "Wyrażenie sugeruje strukturę krzywej eliptycznej.",
    },
    "Yang_Mills": {
        "id": "MP-4",
        "name": "Yang–Mills i luka masowa",
        "status": "OPEN",
        "keywords": [
            r"yang.?mills", r"mass.?gap", r"gauge", r"SU\(2\)", r"SU\(3\)"
        ],
        "description": "Istnienie teorii YM z dodatnią luką masową.",
        "risk": "Wyrażenie dotyczy teorii pola lub grup cechowania.",
    },
    "Navier_Stokes": {
        "id": "MP-5",
        "name": "Równania Naviera–Stokesa",
        "status": "OPEN",
        "keywords": [
            r"navier", r"stokes", r"fluid", r"viscosity", r"turbulence",
            r"velocity", r"pressure"
        ],
        "description": "Istnienie i gładkość rozwiązań NS w R³.",
        "risk": "Wyrażenie zawiera struktury mechaniki płynów.",
    },
    "Poincare": {
        "id": "MP-6",
        "name": "Hipoteza Poincarégo",
        "status": "SOLVED",
        "solved_by": "Grigorij Perelman (2003)",
        "keywords": [
            r"poincare", r"3.?sphere", r"simply.?connected", r"3.?manifold"
        ],
        "description": "Każda 3‑rozmaitość prosta spójnie ≅ S³.",
        "risk": "UWAGA: Problem ROZWIĄZANY — sprawdź, czy wyrażenie nie zakłada jego otwartości.",
    },
    "Hodge": {
        "id": "MP-7",
        "name": "Hipoteza Hodge'a",
        "status": "OPEN",
        "keywords": [
            r"hodge", r"cohomology", r"de.?Rham", r"Dolbeault", r"H\{p,p\}"
        ],
        "description": "Klasy de Rhama są kombinacjami cykli algebraicznych.",
        "risk": "Wyrażenie sugeruje strukturę kohomologiczną.",
    },
}


# ─────────────────────────────────────────────
# Detekcja symboliczna
# ─────────────────────────────────────────────

def _detect_symbolic(sym) -> List[str]:
    if not SYMPY_AVAILABLE or sym is None:
        return []

    hits = []
    s = str(sym)

    # Riemann
    if "zeta" in s:
        hits.append("Riemann")

    # Navier–Stokes — realne klasy SymPy
    if any(k in s for k in ["Gradient", "Divergence", "Laplacian"]):
        hits.append("Navier_Stokes")

    # Yang–Mills — SU(n)
    if re.search(r"SU\(\d+\)", s):
        hits.append("Yang_Mills")

    return hits


# ─────────────────────────────────────────────
# Detekcja słów kluczowych
# ─────────────────────────────────────────────

def _detect_keywords(raw: str) -> List[str]:
    hits = []
    for pid, info in MILLENNIUM_PROBLEMS.items():
        for kw in info["keywords"]:
            if re.search(kw, raw, flags=re.IGNORECASE):
                hits.append(pid)
                break
    return hits


# ─────────────────────────────────────────────
# Wynik filtra
# ─────────────────────────────────────────────

@dataclass
class MillenniumMatch:
    problem_id: str
    name: str
    status: str
    confidence: str
    source: str
    risk: str
    description: str
    solved_by: Optional[str] = None


def _confidence(keyword_hit: bool, symbolic_hit: bool) -> str:
    if keyword_hit and symbolic_hit:
        return "HIGH"
    if symbolic_hit:
        return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────
# Publiczny entry point
# ─────────────────────────────────────────────

def run(parsed) -> dict:
    raw = parsed.raw
    sym = getattr(parsed, "sym", None)

    keyword_hits = set(_detect_keywords(raw))
    symbolic_hits = set(_detect_symbolic(sym))
    all_hits = keyword_hits | symbolic_hits

    matches = []
    for pid in all_hits:
        info = MILLENNIUM_PROBLEMS[pid]
        kw_hit = pid in keyword_hits
        sym_hit = pid in symbolic_hits

        matches.append(MillenniumMatch(
            problem_id=info["id"],
            name=info["name"],
            status=info["status"],
            confidence=_confidence(kw_hit, sym_hit),
            source="both" if (kw_hit and sym_hit) else ("symbolic" if sym_hit else "keyword"),
            risk=info["risk"],
            description=info["description"],
            solved_by=info.get("solved_by"),
        ))

    open_count = sum(1 for m in matches if m.status == "OPEN")
    solved_count = sum(1 for m in matches if m.status == "SOLVED")

    if not matches:
        summary = "Brak powiązań z Problemami Milenijnymi."
    else:
        names = ", ".join(m.name for m in matches)
        summary = f"Wykryto powiązania z: {names}. Otwartych: {open_count}, rozwiązanych: {solved_count}."

    return {
        "triggered": bool(matches),
        "matches": [m.__dict__ for m in matches],
        "summary": summary,
        "open_problems": open_count,
        "solved_problems": solved_count,
    }
