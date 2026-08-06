## 🔗 Wszystkie modele i repozytoria
Pełna lista projektów znajduje się na stronie:
https://jbackk-lang.github.io
---
# math-validator-3.0

`math-validator-2.0` to druga generacja walidatora struktur matematycznych.  
Został zaprojektowany tak, aby wykrywać nie tylko błędy składniowe, ale również
tzw. **problemy mylne** — wyrażenia pozornie poprawne, które są niespójne
w szerszym kontekście logicznym.

---

## 🔧 Funkcje

- analiza składniowa wyrażeń matematycznych,
- wykrywanie sprzeczności,
- klasyfikacja błędów:
  - `OK` — poprawne,
  - `ERROR` — błąd składni lub sprzeczność,
  - `MISLEADING` — problem mylny (pozorna poprawność),
- modułowa architektura (parser → walidator → raport),
- przygotowany pod integrację z TRM / TIMDR (Λ–Τ–Ρ).

---

## 🆚 Różnice względem `math-validator` (1.0)

- przebudowany parser,
- rozszerzona logika błędów,
- dodany typ `MISLEADING`,
- możliwość eksportu wyników do CSV / JSONL,
- przygotowane miejsce na integrację z TRM i TIMDR.

---
Problemy mylne (MISLEADING)
„Problem mylny” to wyrażenie, które:

wygląda poprawnie,

przechodzi podstawową składnię,

ale jest niespójne logicznie lub niejednoznaczne.

Przykłady:

1=1=1

(a=b=c)

0^0=1 (zależne od kontekstu)

## ▶️ Jak używać

Plik wejściowy `input.txt`:


---

# math-validator-2.0

py -3.14 -m pip install uvicorn fastapi

py -3.14 -m uvicorn api:app --reload

uvicorn app:app --reload

http://127.0.0.1:8000/validate?expr=1/(x-1)

## 🧩 Przykłady problemów milenijnych (dla testów walidatora)

Poniżej dwa krótkie przykłady równań związanych z problemami milenijnymi,
które można przepuścić przez `math-validator-2.0` w celu analizy strukturalnej.

### 1. Hipoteza Riemanna
Wyrażenie definiujące funkcję ζ(s):

ζ(s) = ∑_{n=1}^{∞} 1 / n^s


Walidator może wykryć:
- niejednoznaczność dziedziny,
- punkty osobliwe,
- problemy mylne przy złej składni zapisu sumy.

### 2. Równania Naviera–Stokesa
Podstawowa forma równania ruchu płynu:

∂u/∂t + (u · ∇)u = -∇p + νΔu


Walidator może wykryć:
- brak określenia zmiennych,
- niekompletność operatorów,
- strukturalne niespójności w zapisie.

*(To nie są „rozwiązania”, tylko przykłady równań używanych w testach walidatora.)*

Gdy teraz uruchomisz validate("x2"), słownik FILTERS automatycznie wykona powyższe skrypty, a funkcja zwróci pełną strukturę danych gotową do wysłania na Dashboard Geometrii Pola:

JSON
{
  "filters": {
    "information": { ... },
    "syntax": { ... },
    "moebius": {
      "status": "PASSED",
      "metric": "Möbius Parity Invariance",
      "details": "Zachowano ciągłość orientacji Möbiusa."
    },
    "topology": {
      "status": "PASSED",
      "metric": "Triloop Topological Closure",
      "details": "Układ zbieżny topologicznie, brak przerw w strukturze węzłów."
    },
    "singularity": {
      "status": "PASSED",
      "metric": "Singularity & Causality Guard",
      "details": "Brak osobliwości krytycznych. Oś czasu tau zachowuje monotoniczność."
    }
    // ... pozostałe filtry
  },
  "stability": {
    "cycle": 1,
    "angle": 72,
    "phase": "UNDEFINED",
    "orientation": "M_PRIME"
  }
}
