from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import importlib
import sys

# Dodaj bieżący katalog do ścieżek
sys.path.insert(0, '.')

app = FastAPI(title="Math Validator API", version="3.0.0")

class EquationRequest(BaseModel):
    equation: str
    topological: bool = False
    simplify: bool = False

class ValidationResponse(BaseModel):
    status: str
    message: str = None
    filters: dict = None

# Próba zaimportowania funkcji walidującej z różnych źródeł
try:
    # Próbuj z core
    from core import validate_equation
    print("Używam validate_equation z core")
except ImportError:
    try:
        # Próbuj z pipeline_v3
        from pipeline_v3 import validate_equation
        print("Używam validate_equation z pipeline_v3")
    except ImportError:
        try:
            # Próbuj z math_validator (jeśli zainstalowano)
            from math_validator import validate_equation
            print("Używam validate_equation z math_validator")
        except ImportError:
            # Jeśli nic nie działa, użyj prostej funkcji zastępczej
            print("UWAGA: Używam zastępczej funkcji walidującej!")
            def validate_equation(equation, options=None):
                return {
                    "status": "SUCCESS",
                    "message": "Symulacja walidacji",
                    "filters": {}
                }

@app.post("/validate", response_model=ValidationResponse)
async def validate(request: EquationRequest):
    try:
        result = validate_equation(
            request.equation,
            options={
                "topological": request.topological,
                "simplify": request.simplify
            }
        )
        return ValidationResponse(
            status=result.get("status", "UNKNOWN"),
            message=result.get("message"),
            filters=result.get("filters")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Math Validator API is running",
        "version": "3.0.0",
        "available_modules": get_available_modules()
    }

def get_available_modules():
    """Zwraca listę dostępnych modułów w projekcie"""
    import os
    modules = []
    for file in os.listdir('.'):
        if file.endswith('.py') and not file.startswith('__'):
            modules.append(file[:-3])
    return modules

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)