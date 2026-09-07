# math-validator

**Walidator wyrażeń matematycznych: składnia, algebra, logika zdaniowa, jednostki fizyczne i algebra liniowa.**

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

## Opis

`math-validator` sprawdza wyrażenia matematyczne pod kątem błędów, które sama
biblioteka SymPy przepuściłaby bez ostrzeżenia — złej składni, niejednoznacznej
notacji, "cichej" utraty osobliwości przy upraszczaniu, niespójności wymiarowej
(fizyka: metry + sekundy), czy niezgodności wymiarów macierzy przed mnożeniem.

Obsługuje trzy niezależne domeny walidacji:

- **wyrażenia algebraiczne** — `2*x + 3*x`, `(x**2-1)/(x-1)`, `sin(x)^2 + cos(x)^2`
- **formuły logiki zdaniowej** — `(A ∧ B) → C`
- **wyrażenia macierzowe** — `Matrix([[1,2],[3,4]]) * Matrix([[1],[0]])`

## Instalacja

```bash
git clone https://github.com/jbackk-lang/math-validator-3.0.git
cd math-validator-3.0
pip install -e ".[dev]"     # instalacja edytowalna + narzędzia deweloperskie
# albo bez trybu editable:
pip install -r requirements.txt
```
uvicorn api:app --reload
index.html

Wymaga Pythona 3.10+. Zależności runtime rdzenia to tylko `sympy` i `numpy`.
Warstwa HTTP (`api.py`) jest opcjonalna — potrzebuje dodatkowo `fastapi`/`uvicorn`,
instalowanych przez `pip install -e ".[api]"` (patrz sekcja "API HTTP" niżej).

## Szybki start

### Python

```python
from pipeline_v3 import validate_all

result = validate_all("2*x + 3*x")
print(result["status"])                    # "ok"
print(result["normalize"]["normalized"])   # "5*x"
```

```python
# Formuła logiki zdaniowej
result = validate_all("(A ∧ B) → C", formula=True)
print(result["symbolic_logic"]["is_tautology"])   # False

result = validate_all("A ∨ ¬A", formula=True)
print(result["symbolic_logic"]["is_tautology"])   # True
```

```python
# Analiza wymiarowa
from units import analyze_units
r = analyze_units("v*t + 0.5*a*t**2", {"v": "m/s", "t": "s", "a": "m/s**2"})
print(r["status"], r["result_dimension"])   # ok m

r = analyze_units("x + t", {"x": "m", "t": "s"})
print(r["status"])   # error — metry + sekundy
```

```python
# Algebra liniowa
from linalg import validate_matrix_expression
r = validate_matrix_expression("Matrix([[1,2,3],[4,5,6]]) * Matrix([[1,2],[3,4]])")
print(r["status"], r["message"])
# error — nie można pomnożyć macierzy 2x3 przez 2x2 (kolumny lewej != wiersze prawej)
```

Więcej działających przykładów: [`examples/basic_usage.py`](examples/basic_usage.py),
[`examples/topological_analysis.py`](examples/topological_analysis.py).

### CLI

```bash
python cli.py "2+2*3"
python cli.py "x/x" --pretty
python cli.py "(A ∧ B) → C" --formula
python cli.py "Matrix([[1,2]]) * Matrix([[1,2]])" --matrix
python cli.py "v*t" --units v=m/s --units t=s
python cli.py "2*x + 3*x" --normalize-only
python cli.py "x**2 - 4" --solve x
echo "2+2*3" | python cli.py -
```

Po `pip install -e .` dostępne też jako komenda `math-validator`. Flaga
`--fail-on-issues` ustawia kod wyjścia 1, gdy wynik nie jest czysty — przydatne
w CI/CD.

## Co konkretnie wykrywa

| Filtr | Plik | Co sprawdza |
|---|---|---|
| Składnia | `filters/syntax_filter.py` | niedomknięte nawiasy, podwójne operatory, puste nawiasy |
| Algebra | `filters/algebra_filter.py` | podstawowa poprawność algebraiczna |
| Logika (algebraiczna) | `filters/logic_filter.py` | `zoo`/`oo`/`nan` w wyniku wyrażenia |
| Mylące uproszczenia | `filters/misleading_filter.py` | pozornie poprawne, ale niespójne zapisy |
| Harmoniczny | `filters/harmonic_filter.py` | obecność funkcji trygonometrycznych, okresowość |
| Informacyjny | `filters/information_filter.py` | entropia i redundancja symboli w zapisie |
| Numeryczny | `filters/numeric_filter.py` | rozwiązania rzeczywiste vs zespolone |
| Widmo pierwszych | `filters/prime_spectrum_filter.py` | analiza wyrażeń całkowitych pod kątem rozkładu liczb pierwszych |
| Problemy Milenijne | `filters/millennium_filter.py` | wykrywa powiązania wyrażenia z 7 Problemami Milenijnymi (Riemann, P vs NP, Navier-Stokes...) |
| Möbius | `filters/moebius_filter.py` | wykrywa odwrócenia/pętle/transformacje zmieniające orientację wyrażenia |
| Osobliwości | `filters/singularity_filter.py` | osobliwości i skręty τ (lim 0⁺ ≠ lim 0⁻) |
| Topologia | `filters/topology_filter.py` | dziedzina ciągłości wyrażenia (`continuous_domain`) |
| Logika zdaniowa | `filters/symbolic_logic_filter.py` | `(A ∧ B) → C`: tautologia/sprzeczność/spełnialność, CNF/DNF |
| Jednostki | `units.py` | spójność wymiarowa SI (nie doda metrów do sekund) |
| Normalizacja | `normalize.py` | uproszczenie + wykrycie utraconej osobliwości |
| Zmienne | `variables.py` | wolne vs związane (`Sum`, `Integral`, `Derivative`...) |
| Niejednoznaczność | `ambiguity.py` | `a/b*c`, `a^b^c`, `-a^b`, `1/2x` + sugestie nawiasów |
| Algebra liniowa | `linalg.py` | wymiary macierzy przed mnożeniem/dodawaniem/odwracaniem |
| Diagnostyka błędów | `errors.py` | pozycja błędu + "czy chodziło o..." dla literówek w nazwach funkcji |

Wszystkie 12 filtrów z powyższej tabeli (oprócz `symbolic_logic_filter`) jest
spiętych automatycznie przez `pipeline_v3.validate_all()`. `symbolic_logic_filter`
i `linalg` mają osobne tryby wejścia (`formula=True`, `matrix=True`), bo
operują na innej gramatyce niż zwykłe wyrażenia algebraiczne.

`millennium`, `moebius`, `singularity`, `topology` pochodzą z `math-validator-v2.0`
i istniały tam od początku — zniknęły przy pierwszej migracji do v3 (nie
zostały skopiowane), przywrócono je 2026-08-24, patrz `CHANGELOG_v3.md`.

**`prime_spectrum_filter.py` — naprawiony ungruntowany próg (2026-08-26).**
Etykieta `log_spiral_1_over_f` wcześniej pojawiała się przy sztywnym,
arbitralnym progu 0.25 i niosła dopisaną notatkę o zgodności z „TIMDR
Λ–τ–ρ" — bez żadnego wsparcia statystycznego. Naprawiono: próg jest teraz
liczony z modelu zerowego (1000 losowych ciągów o tej samej długości i
zakresie kroków, próg = 5. percentyl). Sprawdzone empirycznie na
niezależnych oknach wzdłuż prawdziwych liczb pierwszych do 10⁶: realne
liczby pierwsze trafiają w tę etykietę **rzadziej** niż losowe ciągi
(0.3%–2.7% wobec oczekiwanych ~5%), nie częściej — czyli filtr nie
wykrywa niczego specyficznego dla liczb pierwszych. Twierdzenie o
związku z TIMDR zostało w związku z tym usunięte z notatek filtra;
klasyfikacja zwraca teraz też `diff_metric` i `null_threshold_5pct`, żeby
wynik był sprawdzalny, nie tylko etykietowy. Patrz testy w
`test/test_prime_spectrum_null_model.py`.

## Rozszerzalność (wtyczki)

Własny filtr bez modyfikowania rdzenia:

```python
import plugins

@plugins.register_filter("moj_filtr")
def run(p):
    return {"status": "ok"}
```

albo automatyczne ładowanie katalogu:

```python
plugins.load_plugins_from_dir("plugins_examples")
```

Przykład: [`plugins_examples/no_negative_sqrt.py`](plugins_examples/no_negative_sqrt.py).

## Struktura repo

```
core.py, parser.py          # parsowanie wyrażeń -> ParsedExpr
algebra.py, logic.py        # cienkie wrappery nad filters/algebra_filter, filters/logic_filter
filters/                    # pojedyncze reguły walidacji, każdy z run(parsed) -> dict
pipeline_v3.py               # spina wszystkie filtry + wtyczki w jedno validate_all()
units.py, normalize.py,     # moduły v3 — patrz CHANGELOG_v3.md po szczegóły
variables.py, ambiguity.py,
linalg.py, errors.py,
sympy_bridge.py, plugins.py
cli.py                      # interfejs linii poleceń
api.py                      # opcjonalna warstwa HTTP (FastAPI) nad validate_all()
examples/                   # działające przykłady użycia API
test/                       # pytest, 28 testów (19 moduły v3 + 9 filtry przywrócone z v2.0)
docs/                       # statyczne materiały (index.html, grafika) — niepodłączone do kodu
```

## API HTTP (opcjonalne)

Poza CLI i użyciem bezpośrednio z Pythona, repo zawiera cienką warstwę HTTP
nad `pipeline_v3.validate_all()`, zbudowaną na FastAPI:

```bash
pip install -e ".[api]"     # doinstaluje fastapi + uvicorn
uvicorn api:app --reload
```

Interaktywna dokumentacja (Swagger UI): http://127.0.0.1:8000/docs
WebGUI strona index.html

Endpointy:

| Metoda | Ścieżka | Co robi |
|---|---|---|
| GET | `/health` | prosty health-check |
| POST | `/validate` | pełna walidacja wyrażenia algebraicznego (opcjonalnie `units`) |
| POST | `/validate/formula` | walidacja formuły logiki zdaniowej |
| POST | `/validate/matrix` | walidacja wyrażenia macierzowego |
| POST | `/solve` | rozwiązuje `wyrażenie = 0` względem zmiennej |
| POST | `/latex` | zwraca zapis LaTeX wyrażenia |
| POST | `/millennium` | sprawdza wyrażenie pod kątem powiązań z 7 Problemami Milenijnymi |
| GET | `/millennium/problems` | statyczny katalog wszystkich 7 Problemów Milenijnych (nazwa, status, opis) |
| POST | `/api/v3/paradox` | wykrywa paradoks logiczny (skali/struktury/założeń/continuum) w sekwencji kroków `steps` |

Przykład:

```bash
curl -X POST http://127.0.0.1:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"expression": "2*x + 3*x"}'
```

`millennium_filter` był od dawna wpięty w `validate_all()`, ale pogrzebany
wśród ~15 innych kluczy pełnej odpowiedzi. Dwa dedykowane endpointy
wystawiają go bezpośrednio:

```bash
curl -X POST http://127.0.0.1:8000/millennium \
  -H "Content-Type: application/json" \
  -d '{"expression": "zeta(1/2 + I*t)"}'
# {"triggered": true, "matches": [{"name": "Hipoteza Riemanna", ...}], ...}

curl http://127.0.0.1:8000/millennium/problems
# {"count": 7, "problems": [{"key": "Riemann", "status": "OPEN", ...}, ...]}
```

Ten samy problem widoczności dotyczył modułu paradoksów
(`paradox_trigger_module.py`): był wpięty do `validate_all()` przez
opcjonalny parametr `steps`, ale ani API, ani WebGUI go nie eksponowały —
w praktyce nieużywalny bez czytania kodu `pipeline_v3.py`. Naprawione tym
samym wzorcem — dedykowany endpoint plus zakładka "Paradoksy" w
`index.html`:

```bash
curl -X POST http://127.0.0.1:8000/api/v3/paradox \
  -H "Content-Type: application/json" \
  -d '{"steps": [{"local_valid": true, "global_valid": false}]}'
# {"triggered": true, "type": "scale", "location": 0, "message": "Local model works, global model breaks (scale paradox)."}
```

## Testy

```bash
pytest -v
```

## Dokumentacja zmian v3

Pełny opis funkcji dodanych w wersji 3 (logika symboliczna, jednostki,
normalizacja, algebra liniowa, CLI, wtyczki, bogatsze błędy) — patrz
[`CHANGELOG_v3.md`](CHANGELOG_v3.md).

## Współpraca

Zobacz [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licencja

MIT — zobacz [`LICENSE`](LICENSE).
