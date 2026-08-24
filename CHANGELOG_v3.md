# math-validator — v3

Rozszerzenie `math-validator-2.0` o funkcje z roadmapy. Pliki poniżej
wpina się do istniejącego repo obok `core.py` i katalogu `filters/`
(v3 korzysta z `core.parse()` / `ParsedExpr` i konwencji
`filters/*.run(parsed) -> dict` już obecnej w v2).

## Instalacja

```bash
pip install sympy numpy fastapi uvicorn
# opcjonalnie: pip install -e .   # rejestruje komendę `math-validator`
```

## Co nowego

### 1. Logika i wnioskowanie
- **`filters/symbolic_logic_filter.py`** — własny parser formuł zdaniowych
  (`∧ ∨ ¬ → ↔ ⊕`, aliasy `& | ! -> <-> ^^`), tabela prawdy, wykrywanie
  tautologii/sprzeczności/spełnialności, eksport do CNF/DNF przez sympy
  (`sympy.logic.boolalg`), gotowe pod integrację z solverami SAT
  (`sympy.logic.inference.satisfiable`, lub eksport do DIMACS).
  Uwaga: to inny moduł niż istniejący `logic.py` z v2 (ten wykrywa `zoo`/`oo`/`nan`
  w wyrażeniach algebraicznych — zostawiony bez zmian).
- **`units.py`** — weryfikacja wymiarowa (SI): sprawdza spójność dodawania,
  mnożenia, potęgowania i argumentów funkcji trygonometrycznych/wykładniczych
  pod kątem wymiarów fizycznych. Nie wymaga zewnętrznych bibliotek (własna
  tablica jednostek bazowych + pochodnych: N, J, W, Pa, Hz, V, Ω...).

### 2. Głębsza analiza i transformacja
- **`normalize.py`** — upraszcza wyrażenia (`simplify/expand/factor/together/
  cancel/trigsimp/...`) i **jawnie raportuje utracone założenia o dziedzinie**
  (np. `(x²-1)/(x-1) → x+1` traci osobliwość w `x=1` — normalize.py to wykrywa
  i ostrzega, analogicznie do `misleading_filter.py` z v2).
- **`variables.py`** — analiza zmiennych wolnych vs związanych (`Sum`,
  `Integral`, `Derivative`, `Limit`, `Product`), wykrywanie przesłonięcia
  (shadowing).
- **`ambiguity.py`** — wykrywa niejednoznaczne zapisy (`a/b*c`, `a^b^c`,
  `-a^b`, `1/2x`), proponuje jednoznaczną parenteizację dla każdej
  interpretacji, oraz **konfigurowalny system priorytetów operatorów**
  (`PrecedenceConfig`: łączność potęgowania, siła niejawnego mnożenia).

### 3. Interfejsy i integracja
- **`cli.py`** — `python cli.py "2+2*3"`, obsługuje `--formula`, `--matrix`,
  `--units v=m/s`, `--normalize-only`, `--solve x`, `--diff x`, `--latex`,
  `--fail-on-issues` (exit code 1 dla CI/CD), wejście ze stdin (`-`).
  Po `pip install -e .` dostępne jako komenda `math-validator`.
- **`sympy_bridge.py`** — `SymPyBridge(expr).solve/diff/integrate/series/
  evalf/latex/solve_equation(...)` — brama do dalszych obliczeń w SymPy
  po walidacji.
- **`linalg.py`** — walidacja wymiarów macierzy/wektorów przed operacją
  (`Matrix([[..]]) * Matrix([[..]])`, dodawanie, wyznacznik, odwracanie),
  z czytelnymi komunikatami typu *"nie można pomnożyć macierzy 2x3 przez
  2x2 — liczba kolumn lewej (3) musi równać się liczbie wierszy prawej (2)"*.

### 4. Ulepszenia jądra
- **`errors.py`** — precyzyjne diagnostyki z pozycją i karetką (`^`),
  np. *"Błąd w pozycji 3: brakujący nawias zamykający po 'sin('"*, plus
  sugestie "czy chodziło o..." dla literówek w nazwach funkcji
  (`difflib.get_close_matches`).
- **`plugins.py`** — mechanizm wtyczek: `@register_filter("nazwa")` albo
  `load_plugins_from_dir(katalog)` — dodawanie własnych filtrów bez
  modyfikacji rdzenia. Przykład: `plugins_examples/no_negative_sqrt.py`.

### Spinacz
- **`pipeline_v3.py`** — `validate_all(expr, ...)` uruchamia wszystkie
  filtry v2 + v3 + zarejestrowane wtyczki w jednym wywołaniu.

## Testy

```bash
pytest test/test_v3.py -v
pytest test/test_restored_filters_v3.py -v
```
19/19 testów `test_v3.py` (logika symboliczna, jednostki, normalizacja,
zmienne, niejednoznaczność, algebra liniowa, diagnostyka błędów, most
sympy, wtyczki) + 9/9 `test_restored_filters_v3.py` (patrz sekcja
"Poprawka: brakujące filtry z v2.0" niżej) = 28/28 razem.

## Poprawka: brakujące filtry z v2.0 (2026-08-24)

Przy migracji z `math-validator-v2.0` do v3 nie skopiowano czterech z
dwunastu filtrów: `filters/millennium_filter.py` (Problemy Milenijne),
`filters/moebius_filter.py` (struktury Möbiusa), `filters/singularity_filter.py`
(osobliwości i skręty τ) oraz `filters/topology_filter.py` (dziedzina
ciągłości). W efekcie v3, mimo że w tym pliku i w README opisywana jest
jako rozszerzenie v2 ("wersja poprawiona i rozbudowana"), faktycznie miała
mniej filtrów niż v2 — nie była jej nadzbiorem. Poprawiono: pliki
skopiowane 1:1 (core.py jest identyczny w obu wersjach, więc interfejs
`run(parsed: ParsedExpr) -> dict` jest w pełni kompatybilny bez zmian),
wpięte do `pipeline_v3.validate_all()` pod kluczami `millennium`,
`moebius`, `singularity`, `topology`, dodane testy integracyjne.

Dodatkowo: `pyproject.toml` miał nieprawidłowy TOML — `[tool.setuptools]`
z jawną listą `packages = [...]` współistniał z `[tool.setuptools.packages.find]`
(dwie wykluczające się metody konfiguracji tej samej tabeli), co blokowało
`pip install -e .` i uruchomienie `pytest` w ogóle (błąd parsera: "Cannot
declare ('tool', 'setuptools', 'packages', 'find') twice"). Usunięto
sprzeczny blok auto-wykrywania, zostawiając jawną listę.

## Znane ograniczenia / uwagi dla dalszej pracy
- `units.py` zakłada, że zmienna bez podanej jednostki jest bezwymiarowa —
  dla pełnej rygorystyczności warto by wymuszać podanie jednostek dla
  wszystkich symboli w wyrażeniu (obecnie to świadomy kompromis UX).
- `ambiguity.py` operuje na wzorcach regex na surowym stringu (celowo —
  żeby wykryć niejednoznaczność *przed* tym, jak Python/sympy już ją
  rozstrzygnie przy parsowaniu). To działa dobrze dla prostych przypadków;
  dla w pełni ogólnego rozwiązania warto rozważyć własny tokenizer.
- POPRAWKA (2026-08-24): poprzednia wersja tego pliku twierdziła, że repo
  zawiera dodatkowo osobną "warstwę pseudofizycznych metafor" (`topology.py`,
  `moebius_parity.py`, `entropy_flow.py`, `lambda_stabilizer.py`,
  `khipu_knot_check.py`). Sprawdzono bezpośrednio w repozytorium — żaden
  z tych plików nie istnieje nigdzie w drzewie katalogów. To była
  nieaktualna/błędna dokumentacja, nie rzeczywisty stan kodu — usunięto
  fałszywe twierdzenie zamiast je powielać.
