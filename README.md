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

## Instalacja i szybkie uruchomienie

Wymaga Pythona 3.10+. Zależności runtime rdzenia to tylko `sympy` i `numpy`.

### 🚀 Szybki start (Windows) — automatyczne uruchomienie
Najprostszym sposobem na uruchomienie aplikacji (zarówno serwera API, jak i interfejsu WebGUI w przeglądarce) na systemie Windows jest użycie dołączonego skryptu **`run.bat`**:

1. Pobierz / sklonuj repozytorium:
   ```bash
   git clone [https://github.com/jbackk-lang/math-validator-3.0.git](https://github.com/jbackk-lang/math-validator-3.0.git)
   cd math-validator-3.0
