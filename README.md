# math-validator 3.0
**Walidator wyrażeń matematycznych: składnia, algebra, logika zdaniowa, jednostki fizyczne i algebra liniowa.**

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

## Opis

math-validator 3.0 wykrywa błędy, które SymPy przepuszcza bez ostrzeżenia: złą składnię, niejednoznaczność zapisu, utratę osobliwości przy upraszczaniu, niespójność wymiarową (metry + sekundy), błędne wymiary macierzy przed mnożeniem oraz sprzeczne formuły logiki zdaniowej.

Obsługiwane domeny:
- Algebraiczne wyrażenia
- Logika zdaniowa
- Algebra liniowa

## Instalacja

Wymagany Python 3.10+.  
Zależności runtime: sympy, numpy.

### Windows — szybki start (run.bat)

1. Pobierz repozytorium:
   git clone https://github.com/jbackk-lang/math-validator-3.0.git
   cd math-validator-3.0

2. Uruchom run.bat.

Skrypt:
- instaluje brakujące pakiety,
- uruchamia API (python -m uvicorn api:app),
- otwiera WebGUI (index.html).

### Linux / macOS

git clone https://github.com/jbackk-lang/math-validator-3.0.git
cd math-validator-3.0
pip install -e ".[dev]"
# lub:
pip install -r requirements.txt

Warstwa HTTP:
pip install -e ".[api]"

## Szybki start — Python

### Algebra
from pipeline_v3 import validate_all

result = validate_all("2*x + 3*x")
print(result["status"])
print(result["normalize"]["normalized"])

### Logika zdaniowa
result = validate_all("(A ∧ B) → C", formula=True)
print(result["symbolic_logic"]["is_tautology"])

result = validate_all("A ∨ ¬A", formula=True)
print(result["symbolic_logic"]["is_tautology"])

### Jednostki fizyczne
from units import analyze_units
r = analyze_units("v*t + 0.5*a*t**2", {"v": "m/s", "t": "s", "a": "m/s**2"})
print(r["status"], r["result_dimension"])

r = analyze_units("x + t", {"x": "m", "t": "s"})
print(r["status"])

### Algebra liniowa
from linalg import validate_matrix_expression
r = validate_matrix_expression("Matrix([[1,2,3],[4,5,6]]) * Matrix([[1,2],[3,4]])")
print(r["status"], r["message"])

## CLI

python cli.py "2+2*3"
python cli.py "x/x" --pretty
python cli.py "(A ∧ B) → C" --formula
python cli.py "Matrix([[1,2]]) * Matrix([[1,2]])" --matrix
python cli.py "v*t" --units v=m/s --units t=s
python cli.py "2*x + 3*x" --normalize-only
python cli.py "x**2 - 4" --solve x
echo "2+2*3" | python cli.py -

Po instalacji:
math-validator "2+2*3"

## Co wykrywa?

Składnia — filters/syntax_filter.py  
Algebra — filters/algebra_filter.py  
Logika algebraiczna — filters/logic_filter.py  
Mylące uproszczenia — filters/misleading_filter.py  
Harmoniczny — filters/harmonic_filter.py  
Informacyjny — filters/information_filter.py  
Numeryczny — filters/numeric_filter.py  
Widmo liczb pierwszych — filters/prime_spectrum_filter.py  
Logika zdaniowa — filters/symbolic_logic_filter.py  
Jednostki SI — units.py  
Normalizacja — normalize.py  
Zmienne — variables.py  
Niejednoznaczność — ambiguity.py  
Algebra liniowa — linalg.py  
Diagnostyka błędów — errors.py  

## Wtyczki

import plugins

@plugins.register_filter("moj_filtr")
def run(p):
    return {"status": "ok"}

plugins.load_plugins_from_dir("plugins_examples")

## Struktura repozytorium

core.py, parser.py  
algebra.py, logic.py  
filters/  
pipeline_v3.py  
units.py, normalize.py  
variables.py, ambiguity.py  
linalg.py, errors.py  
sympy_bridge.py, plugins.py  
cli.py  
api.py  
run.bat  
examples/  
test/  
docs/

## API HTTP & WebGUI

Windows:
run.bat → WebGUI + API pod http://127.0.0.1:8000

Ręcznie:
pip install -e ".[api]"
python -m uvicorn api:app --reload

Swagger UI:
http://127.0.0.1:8000/docs

Endpointy:
GET /health  
POST /validate  
POST /validate/formula  
POST /validate/matrix  
POST /solve  
POST /latex  

## Testy

pytest -v

## Licencja

MIT — patrz LICENSE.
