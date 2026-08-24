"""
api.py — Nowoczesny i czytelny interfejs REST API (FastAPI) dla math-validator v3.

Uruchomienie:
    uvicorn api:app --reload

Dokumentacja Swagger UI:
    http://127.0.0.1:8000/docs
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Path, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Importy wewnętrznych modułów walidatora
from ambiguity import PrecedenceConfig, find_ambiguities
from core import parse
from errors import diagnose_syntax
from filters.millennium_filter import MILLENNIUM_PROBLEMS, run as run_millennium
from linalg import validate_matrix_expression
from normalize import normalize_expression
from pipeline_v3 import validate_all
from sympy_bridge import SymPyBridge

# ==============================================================================
# KONFIGURACJA APLIKACJI
# ==============================================================================

app = FastAPI(
    title="Math Validator API",
    description=(
        "Zaawansowane API do topologicznej i symbolicznej walidacji równań "
        "matematycznych, algebry liniowej, logiki zdaniowej oraz analizy wymiarowej."
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Walidacja", "description": "Główne punkty końcowe analizy wyrażeń."},
        {"name": "Przekształcenia", "description": "Normalizacja, rozwiązywanie i pochodne."},
        {"name": "Diagnostyka", "description": "Analiza niejednoznaczności i błędów składni."},
        {"name": "Problemy Milenijne", "description": "Wykrywanie powiązań wyrażenia z 7 Problemami Milenijnymi."},
        {"name": "System", "description": "Status działania usługi."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# SCHEMATY PYDANTIC (DTO)
# ==============================================================================

class BaseResponse(BaseModel):
    status: str = Field(..., description="Status operacji: 'ok' lub 'error'")
    expression: str = Field(..., description="Analizowane wyrażenie wejściowe")

class ValidateRequest(BaseModel):
    expression: str = Field(..., examples=["(v * t) / 2"], description="Wyrażenie do zwalidowania")
    units: Optional[Dict[str, str]] = Field(
        default=None,
        examples=[{"v": "m/s", "t": "s"}],
        description="Słownik jednostek fizycznych przypisanych do zmiennych"
    )
    implicit_mult_binds_tighter: bool = Field(
        default=False,
        description="Czy mnożenie niejawne (np. 2x) wiąże silniej niż dzielenie (/)"
    )
    power_left_assoc: bool = Field(
        default=False,
        description="Prawostronna (a^b^c = a^(b^c)) vs lewostronna łączność potęgowania"
    )

class FormulaRequest(BaseModel):
    formula: str = Field(..., examples=["(A ∧ B) → C"], description="Formuła logiki zdaniowej")

class MatrixRequest(BaseModel):
    expression: str = Field(
        ...,
        examples=["Matrix([[1,2],[3,4]]) * Matrix([[1],[0]])"],
        description="Wyrażenie macierzowe w formacie SymPy"
    )

class SolveRequest(BaseModel):
    expression: str = Field(..., examples=["2*x + 5 - 11"], description="Równanie równe 0")
    variable: str = Field(default="x", examples=["x"], description="Zmienna, względem której rozwiązujemy")

class NormalizeRequest(BaseModel):
    expression: str = Field(..., examples=["2*x + 3*x + x/x"], description="Wyrażenie do uproszczenia")
    symbol: str = Field(default="x", description="Główna zmienna dziedziny")

class AmbiguityRequest(BaseModel):
    expression: str = Field(..., examples=["1/2x"], description="Wyrażenie potencjalnie niejednoznaczne")
    implicit_mult_binds_tighter: bool = False
    power_left_assoc: bool = False

class MillenniumRequest(BaseModel):
    expression: str = Field(
        ...,
        examples=["zeta(1/2 + I*t)"],
        description="Wyrażenie sprawdzane pod kątem powiązań z Problemami Milenijnymi"
    )

# ==============================================================================
# ENDPOINTY SYSTEMOWE
# ==============================================================================

@app.get("/health", tags=["System"], summary="Sprawdzenie stanu API")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "math-validator", "version": "3.0.0"}

# ==============================================================================
# ENDPOINTY WALIDACJI
# ==============================================================================

@app.post("/api/v3/validate", tags=["Walidacja"], summary="Pełna walidacja wyrażenia")
def validate_expression(req: ValidateRequest) -> Dict[str, Any]:
    """
    Przeprowadza pełny proces walidacji składniowej, algebry, logiki oraz jednostek.
    """
    config = PrecedenceConfig(
        implicit_mult_binds_tighter=req.implicit_mult_binds_tighter,
        power_associativity="left" if req.power_left_assoc else "right",
    )
    try:
        return validate_all(req.expression, units=req.units, precedence_config=config)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Błąd przetwarzania wyrażenia: {str(err)}"
        )

@app.post("/api/v3/validate/formula", tags=["Walidacja"], summary="Walidacja logiki zdaniowej")
def validate_formula(req: FormulaRequest) -> Dict[str, Any]:
    """Sprawdza poprawność formuł logiki zdaniowej (np. z użyciem ∧, ∨, →)."""
    try:
        return validate_all(req.formula, formula=True)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Błąd walidacji formuły: {str(err)}"
        )

@app.post("/api/v3/validate/matrix", tags=["Walidacja"], summary="Walidacja algebry liniowej")
def validate_matrix(req: MatrixRequest) -> Dict[str, Any]:
    """Weryfikuje zgodność wymiarów macierzy i operacji (mnożenie, dodawanie, odwracanie)."""
    result = validate_matrix_expression(req.expression)
    if result.get("status") == "error" and "błąd parsowania" in result.get("message", ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return result

# ==============================================================================
# ENDPOINTY PRZEKSZTAŁCEŃ SYMBOLICZNYCH
# ==============================================================================

@app.post("/api/v3/solve", tags=["Przekształcenia"], summary="Rozwiązywanie równania")
def solve_equation(req: SolveRequest) -> Dict[str, Any]:
    """Wyznacza pierwiastki równania przy założeniu `wyrażenie = 0`."""
    try:
        return SymPyBridge(req.expression).solve(req.variable)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

@app.post("/api/v3/diff", tags=["Przekształcenia"], summary="Różniczkowanie symboliczne")
def calculate_derivative(req: SolveRequest) -> Dict[str, Any]:
    """Oblicza pochodną wyrażenia po wskazanej zmiennej."""
    try:
        return SymPyBridge(req.expression).diff(req.variable)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

@app.post("/api/v3/normalize", tags=["Przekształcenia"], summary="Normalizacja i upraszczanie")
def normalize(req: NormalizeRequest) -> Dict[str, Any]:
    """Upraszcza wyrażenie symbolicznie i śledzi ewentualne zmiany w dziedzinie."""
    res = normalize_expression(req.expression, symbol=req.symbol)
    if res.get("status") == "error":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.get("message"))
    return res

@app.post("/api/v3/render/latex", tags=["Przekształcenia"], summary="Konwersja do formatu LaTeX")
def convert_to_latex(req: SolveRequest) -> Dict[str, Any]:
    """Generuje kod LaTeX reprezentujący podane wyrażenie."""
    try:
        return SymPyBridge(req.expression).latex()
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

# ==============================================================================
# ENDPOINTY DIAGNOSTYCZNE
# ==============================================================================

@app.post("/api/v3/diagnose/ambiguity", tags=["Diagnostyka"], summary="Wykrywanie niejednoznaczności")
def check_ambiguity(req: AmbiguityRequest) -> Dict[str, Any]:
    """Wykrywa pułapki zapisu (np. `1/2x`, `a^b^c`, `-a^b`) oraz proponuje jednoznaczne nawiasowanie."""
    config = PrecedenceConfig(
        implicit_mult_binds_tighter=req.implicit_mult_binds_tighter,
        power_associativity="left" if req.power_left_assoc else "right",
    )
    return find_ambiguities(req.expression, config=config)

@app.get("/api/v3/diagnose/syntax", tags=["Diagnostyka"], summary="Diagnostyka błędów składniowych")
def check_syntax(expr: str = Query(..., examples=["sin(x + 2"])) -> Dict[str, Any]:
    """Wskazuje dokładną pozycję błędu składniowego wraz z czytelnym wskaźnikiem i podpowiedzią."""
    return diagnose_syntax(expr)

# ==============================================================================
# ENDPOINTY PROBLEMÓW MILENIJNYCH
# ==============================================================================
# UWAGA: filters/millennium_filter.py był już od dawna wpięty w validate_all()
# (klucz "millennium" w pełnej odpowiedzi /api/v3/validate), ale pogrzebany
# wśród ~15 innych kluczy - łatwo go było przeoczyć. Poniższe dwa endpointy
# eksponują go bezpośrednio: jeden do sprawdzenia konkretnego wyrażenia,
# drugi jako statyczny katalog wszystkich 7 problemów (do zbudowania np.
# listy/tooltipów we froncie bez konieczności wysyłania wyrażenia).

@app.post(
    "/api/v3/millennium",
    tags=["Problemy Milenijne"],
    summary="Sprawdź powiązanie wyrażenia z Problemami Milenijnymi",
)
def check_millennium(req: MillenniumRequest) -> Dict[str, Any]:
    """
    Analizuje wyrażenie pod kątem słów kluczowych i struktur symbolicznych
    powiązanych z 7 Problemami Milenijnymi (P vs NP, hipoteza Riemanna,
    Bircha-Swinnertona-Dyera, Yang-Mills, Naviera-Stokesa, Poincarégo,
    Hodge'a). Działa nawet gdy wyrażenie się nie sparsuje symbolicznie -
    detekcja słów kluczowych operuje na surowym tekście.
    """
    parsed = parse(req.expression)
    return run_millennium(parsed)

@app.get(
    "/api/v3/millennium/problems",
    tags=["Problemy Milenijne"],
    summary="Katalog wszystkich 7 Problemów Milenijnych",
)
def list_millennium_problems() -> Dict[str, Any]:
    """Zwraca statyczną listę wszystkich Problemów Milenijnych (nazwa, status
    OPEN/SOLVED, opis, słowa kluczowe) - bez analizy żadnego wyrażenia."""
    return {
        "count": len(MILLENNIUM_PROBLEMS),
        "problems": [
            {"key": key, **{k: v for k, v in info.items() if k != "keywords"}}
            for key, info in MILLENNIUM_PROBLEMS.items()
        ],
    }