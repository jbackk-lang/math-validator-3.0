math-validator 3.0
Walidator wyrażeń matematycznych: składnia, algebra, logika zdaniowa, jednostki fizyczne i algebra liniowa.

[Wygląda na to, że wynik nie był bezpieczny do pokazania. Zmieńmy coś i spróbujmy czegoś innego!]
[Wygląda na to, że wynik nie był bezpieczny do pokazania. Zmieńmy coś i spróbujmy czegoś innego!]

Opis
math-validator 3.0 wykrywa błędy, które SymPy przepuszcza bez ostrzeżenia:
złą składnię, niejednoznaczność zapisu, utratę osobliwości przy upraszczaniu, niespójność wymiarową (metry + sekundy), błędne wymiary macierzy przed mnożeniem, czy sprzeczne formuły logiki zdaniowej.

Obsługiwane są trzy niezależne domeny:

Algebraiczne wyrażenia — 2*x + 3*x, (x**2-1)/(x-1)

Logika zdaniowa — (A ∧ B) → C

Algebra liniowa — Matrix([[1,2],[3,4]]) * Matrix([[1],[0]])

Instalacja
Wymagany Python 3.10+.
Zależności runtime: sympy, numpy.

Windows — szybki start (run.bat)
Pobierz repozytorium:

bash
git clone https://github.com/jbackk-lang/math-validator-3.0.git
cd math-validator-3.0
Uruchom run.bat (dwuklik lub cmd).

run.bat wykonuje:

instalację brakujących pakietów (fastapi, uvicorn, pydantic, sympy),

uruchomienie serwera API (python -m uvicorn api:app),

otwarcie WebGUI (index.html) w przeglądarce.

Linux / macOS / CLI
bash
git clone https://github.com/jbackk-lang/math-validator-3.0.git
cd math-validator-3.0
pip install -e ".[dev]"      # tryb developerski
# lub:
pip install -r requirements.txt
Warstwa HTTP (FastAPI) wymaga:

bash
pip install -e ".[api]"
Szybki start — Python
Algebra
python
from pipeline_v3 import validate_all

result = validate_all("2*x + 3*x")
print(result["status"])                     # ok
print(result["normalize"]["normalized"])    # 5*x
Logika zdaniowa
python
result = validate_all("(A ∧ B) → C", formula=True)
print(result["symbolic_logic"]["is_tautology"])  # False

result = validate_all("A ∨ ¬A", formula=True)
print(result["symbolic_logic"]["is_tautology"])  # True
Jednostki fizyczne
python
from units import analyze_units
r = analyze_units("v*t + 0.5*a*t**2", {"v": "m/s", "t": "s", "a": "m/s**2"})
print(r["status"], r["result_dimension"])   # ok m

r = analyze_units("x + t", {"x": "m", "t": "s"})
print(r["status"])                          # error
Algebra liniowa
python
from linalg import validate_matrix_expression
r = validate_matrix_expression("Matrix([[1,2,3],[4,5,6]]) * Matrix([[1,2],[3,4]])")
print(r["status"], r["message"])
# error — niezgodne wymiary (2x3) * (2x2)
CLI
bash
python cli.py "2+2*3"
python cli.py "x/x" --pretty
python cli.py "(A ∧ B) → C" --formula
python cli.py "Matrix([[1,2]]) * Matrix([[1,2]])" --matrix
python cli.py "v*t" --units v=m/s --units t=s
python cli.py "2*x + 3*x" --normalize-only
python cli.py "x**2 - 4" --solve x
echo "2+2*3" | python cli.py -
Po instalacji:

bash
math-validator "2+2*3"
Co wykrywa?
Filtr	Plik	Zakres
Składnia	filters/syntax_filter.py	niedomknięte nawiasy, podwójne operatory
Algebra	filters/algebra_filter.py	poprawność algebraiczna
Logika algebraiczna	filters/logic_filter.py	NaN, zoo, oo
Mylące uproszczenia	filters/misleading_filter.py	utrata osobliwości
Harmoniczny	filters/harmonic_filter.py	okresowość trygonometrii
Informacyjny	filters/information_filter.py	entropia symboli
Numeryczny	filters/numeric_filter.py	rzeczywiste vs zespolone
Widmo liczb pierwszych	filters/prime_spectrum_filter.py	analiza całkowitoliczbowa
Logika zdaniowa	filters/symbolic_logic_filter.py	CNF/DNF, tautologie
Jednostki SI	units.py	spójność wymiarowa
Normalizacja	normalize.py	uproszczenia + osobliwości
Zmienne	variables.py	wolne vs związane
Niejednoznaczność	ambiguity.py	a/b*c, a^b^c, brak nawiasów
Algebra liniowa	linalg.py	wymiary macierzy
Diagnostyka błędów	errors.py	pozycja błędu, sugestie


Pierwszych 8 filtrów jest spiętych przez pipeline_v3.validate_all().

Wtyczki (plugins)
Dodanie własnego filtra:

python
import plugins

@plugins.register_filter("moj_filtr")
def run(p):
    return {"status": "ok"}
Automatyczne ładowanie katalogu:

python
plugins.load_plugins_from_dir("plugins_examples")
Przykład: plugins_examples/no_negative_sqrt.py.

Struktura repozytorium
Kod
core.py, parser.py          # parser wyrażeń -> ParsedExpr
algebra.py, logic.py        # wrappery nad filtrami
filters/                    # pojedyncze reguły walidacji
pipeline_v3.py              # główna funkcja validate_all()
units.py, normalize.py
variables.py, ambiguity.py
linalg.py, errors.py
sympy_bridge.py, plugins.py
cli.py                      # interfejs CLI
api.py                      # warstwa HTTP (FastAPI)
run.bat                     # launcher Windows
examples/                   # przykłady
test/                       # pytest (19 testów)
docs/                       # statyczne materiały
API HTTP & WebGUI
Uruchamianie
Windows:  
Uruchom run.bat → WebGUI + API pod http://127.0.0.1:8000.

Ręcznie:

bash
pip install -e ".[api]"
python -m uvicorn api:app --reload
Otwórz index.html w przeglądarce.

Swagger UI
http://127.0.0.1:8000/docs

Endpointy
Metoda	Ścieżka	Opis
GET	/health	health-check
POST	/validate	algebra + opcjonalnie units
POST	/validate/formula	logika zdaniowa
POST	/validate/matrix	algebra liniowa
POST	/solve	rozwiązywanie równania
POST	/latex	konwersja do LaTeX


Testy
bash
pytest -v
Licencja
MIT — patrz LICENSE.
