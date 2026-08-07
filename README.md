# math-validator 3.0

**Walidator wyrażeń matematycznych: składnia, algebra, logika zdaniowa, jednostki fizyczne i algebra liniowa.**

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

## Opis

`math-validator 3.0` sprawdza wyrażenia matematyczne pod kątem błędów, które sama
biblioteka SymPy przepuściłaby bez ostrzeżenia — złej składni, niejednoznacznej
notacji, "cichej" utraty osobliwości przy upraszczaniu, niespójności wymiarowej
(fizyka: metry + sekundy), czy niezgodności wymiarów macierzy przed mnożeniem.

Obsługuje trzy niezależne domeny walidacji:

- **wyrażenia algebraiczne** — `2*x + 3*x`, `(x**2-1)/(x-1)`, `sin(x)^2 + cos(x)^2`
- **formuły logiki zdaniowej** — `(A ∧ B) → C`
- **wyrażenia macierzowe** — `Matrix([[1,2],[3,4]]) * Matrix([[1],[0]])`

## Instalacja i szybkie uruchomienie

Wymaga Pythona 3.10+. Zależności runtime rdzenia to tylko `sympy` i `numpy`.

### 🚀 Szybki start (Windows) — automatyczne uruchomienie
Najprostszym sposobem na uruchomienie aplikacji (zarówno serwera API, jak i interfejsu WebGUI w przeglądarce) na systemie Windows jest użycie dołączonego skryptu **`run.bat`**:

1. Pobierz / sklonuj repozytorium:
   ```bash
   git clone [https://github.com/jbackk-lang/math-validator-3.0.git](https://github.com/jbackk-lang/math-validator-3.0.git)
   cd math-validator-3.0
Dwukrotnie kliknij plik run.bat (lub uruchom go w konsoli cmd).Co robi run.bat?Automatycznie instaluje i weryfikuje brakujące pakiety (fastapi, uvicorn, pydantic, sympy).Otwiera interfejs graficzny (index.html) w domyślnej przeglądarce.Uruchamia serwer backendowy API za pomocą bezpiecznego wywołania python -m uvicorn api:app (co zapobiega blokadom Windows Device Guard / AppLocker).💻 Instalacja ręczna (Linux / macOS / Python CLI)Bashgit clone [https://github.com/jbackk-lang/math-validator-3.0.git](https://github.com/jbackk-lang/math-validator-3.0.git)
cd math-validator-3.0
pip install -e ".[dev]"     # instalacja edytowalna + narzędzia deweloperskie
# albo bez trybu editable:
pip install -r requirements.txt
Warstwa HTTP (api.py) jest opcjonalna — potrzebuje dodatkowo fastapi/uvicorn,
instalowanych przez pip install -e ".[api]" (patrz sekcja "API HTTP" niżej).Szybki startPythonPythonfrom pipeline_v3 import validate_all

result = validate_all("2*x + 3*x")
print(result["status"])                 # "ok"
print(result["normalize"]["normalized"])   # "5*x"
Python# Formuła logiki zdaniowej
result = validate_all("(A ∧ B) → C", formula=True)
print(result["symbolic_logic"]["is_tautology"])   # False

result = validate_all("A ∨ ¬A", formula=True)
print(result["symbolic_logic"]["is_tautology"])   # True
Python# Analiza wymiarowa
from units import analyze_units
r = analyze_units("v*t + 0.5*a*t**2", {"v": "m/s", "t": "s", "a": "m/s**2"})
print(r["status"], r["result_dimension"])   # ok m

r = analyze_units("x + t", {"x": "m", "t": "s"})
print(r["status"])   # error — metry + sekundy
Python# Algebra liniowa
from linalg import validate_matrix_expression
r = validate_matrix_expression("Matrix([[1,2,3],[4,5,6]]) * Matrix([[1,2],[3,4]])")
print(r["status"], r["message"])
# error — nie można pomnożyć macierzy 2x3 przez 2x2 (kolumny lewej != wiersze prawej)
Więcej działających przykładów: examples/basic_usage.py,examples/topological_analysis.py.CLIBashpython cli.py "2+2*3"
python cli.py "x/x" --pretty
python cli.py "(A ∧ B) → C" --formula
python cli.py "Matrix([[1,2]]) * Matrix([[1,2]])" --matrix
python cli.py "v*t" --units v=m/s --units t=s
python cli.py "2*x + 3*x" --normalize-only
python cli.py "x**2 - 4" --solve x
echo "2+2*3" | python cli.py -
Po pip install -e . dostępne też jako komenda math-validator. Flaga
--fail-on-issues ustawia kod wyjścia 1, gdy wynik nie jest czysty — przydatne
w CI/CD.Co konkretnie wykrywaFiltrPlikCo sprawdzaSkładniafilters/syntax_filter.pyniedomknięte nawiasy, podwójne operatory, puste nawiasyAlgebrafilters/algebra_filter.pypodstawowa poprawność algebraicznaLogika (algebraiczna)filters/logic_filter.pyzoo/oo/nan w wyniku wyrażeniaMylące uproszczeniafilters/misleading_filter.pypozornie poprawne, ale niespójne zapisyHarmonicznyfilters/harmonic_filter.pyobecność funkcji trygonometrycznych, okresowośćInformacyjnyfilters/information_filter.pyentropia i redundancja symboli w zapisieNumerycznyfilters/numeric_filter.pyrozwiązania rzeczywiste vs zespoloneWidmo pierwszychfilters/prime_spectrum_filter.pyanaliza wyrażeń całkowitych pod kątem rozkładu liczb pierwszychLogika zdaniowafilters/symbolic_logic_filter.py(A ∧ B) → C: tautologia/sprzeczność/spełnialność, CNF/DNFJednostkiunits.pyspójność wymiarowa SI (nie doda metrów do sekund)Normalizacjanormalize.pyuproszczenie + wykrycie utraconej osobliwościZmiennevariables.pywolne vs związane (Sum, Integral, Derivative...)Niejednoznacznośćambiguity.pya/b*c, a^b^c, -a^b, 1/2x + sugestie nawiasówAlgebra liniowalinalg.pywymiary macierzy przed mnożeniem/dodawaniem/odwracaniemDiagnostyka błędówerrors.pypozycja błędu + "czy chodziło o..." dla literówek w nazwach funkcjiPierwszych osiem filtrów jest spiętych automatycznie przez pipeline_v3.validate_all().symbolic_logic_filter i linalg mają osobne tryby wejścia (formula=True,matrix=True), bo operują na innej gramatyce niż zwykłe wyrażenia algebraiczne.Rozszerzalność (wtyczki)Własny filtr bez modyfikowania rdzenia:Pythonimport plugins

@plugins.register_filter("moj_filtr")
def run(p):
    return {"status": "ok"}
albo automatyczne ładowanie katalogu:Pythonplugins.load_plugins_from_dir("plugins_examples")
Przykład: plugins_examples/no_negative_sqrt.py.Struktura repocore.py, parser.py          # parsowanie wyrażeń -> ParsedExpr
algebra.py, logic.py        # cienkie wrappery nad filters/algebra_filter, filters/logic_filter
filters/                    # pojedyncze reguły walidacji, każdy z run(parsed) -> dict
pipeline_v3.py               # spina wszystkie filtry + wtyczki w jedno validate_all()
units.py, normalize.py,     # moduły v3 — patrz CHANGELOG_v3.md po szczegóły
variables.py, ambiguity.py,
linalg.py, errors.py,
sympy_bridge.py, plugins.py
cli.py                      # interfejs linii poleceń
api.py                      # opcjonalna warstwa HTTP (FastAPI) nad validate_all()
run.bat                     # automatyczny launcher pod systemy Windows (WebGUI + API)
examples/                   # działające przykłady użycia API
test/                       # pytest, 19 testów pokrywających wszystkie moduły v3
docs/                       # statyczne materiały (index.html, grafika) — niepodłączone do kodu
API HTTP & WebGUIPoza CLI i użyciem bezpośrednio z Pythona, repo zawiera cienką warstwę HTTP nad pipeline_v3.validate_all(), zbudowaną na FastAPI oraz interfejs graficzny WebGUI (index.html).UruchamianieAutomatycznie (Windows): Uruchom plik run.bat — otworzy WebGUI i uruchomi serwer API pod adresem http://127.0.0.1:8000.Ręcznie:Bashpip install -e ".[api]"     # doinstaluje fastapi + uvicorn
python -m uvicorn api:app --reload
Następnie otwórz plik index.html w przeglądarce.Interaktywna dokumentacja API (Swagger UI): http://127.0.0.1:8000/docsEndpointy API:MetodaŚcieżkaCo robiGET/healthprosty health-checkPOST/validatepełna walidacja wyrażenia algebraicznego (opcjonalnie units)POST/validate/formulawalidacja formuły logiki zdaniowejPOST/validate/matrixwalidacja wyrażenia macierzowegoPOST/solverozwiązuje wyrażenie = 0 względem zmiennejPOST/latexzwraca zapis LaTeX wyrażeniaPrzykład zapytania:Bashcurl -X POST [http://127.0.0.1:8000/validate](http://127.0.0.1:8000/validate) \
  -H "Content-Type: application/json" \
  -d '{"expression": "2*x + 3*x"}'
TestyBashpytest -v
Dokumentacja zmian v3Pełny opis funkcji dodanych w wersji 3 (logika symboliczna, jednostki,
normalizacja, algebra liniowa, CLI, wtyczki, bogatsze błędy) — patrz
CHANGELOG_v3.md.WspółpracaZobacz CONTRIBUTING.md.LicencjaMIT — zobacz LICENSE.
