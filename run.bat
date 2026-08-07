@echo off
title Math Validator Studio v3 Launcher

echo ===================================================
echo   Math Validator Studio v3 - Launcher
echo ===================================================
echo.

:: 1. Przejscie do katalogu skryptu
cd /d "%~dp0"

:: 2. Weryfikacja i automatyczna instalacja zaleznosci Pythona
echo [1/3] Sprawdzanie i instalacja wymaganych pakietow...
python -m pip install --quiet fastapi uvicorn pydantic sympy

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Nie udalo sie zainstalowac pakietow. Upewnij sie, ze Python jest w PATH.
    pause
    exit /b %ERRORLEVEL%
)

:: 3. Otwarcie interfejsu HTML w domyslnej przegladarce
echo [2/3] Otwieranie interfejsu aplikacji w przegladarce...
start "" "index.html"

:: 4. Uruchomienie serwera backendu API w Pythonie (FastAPI / Uvicorn)
echo [3/3] Uruchamianie serwera API na http://127.0.0.1:8000 ...
echo.
echo Nacisnij CTRL+C, aby zatrzymac serwer API.
echo ---------------------------------------------------

python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
pause