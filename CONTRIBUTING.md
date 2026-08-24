```markdown
# Zasady Współpracy – math-validator-2.0

Dziękujemy za zainteresowanie projektem! Poniżej znajdziesz zasady, które pomogą nam wspólnie rozwijać `math-validator-2.0`.

---

## 🐛 Zgłaszanie Błędów

1. Sprawdź, czy problem nie został już zgłoszony w [Issues](https://github.com/jbackk-lang/math-validator-2.0/issues).
2. Utwórz nowy issue z opisem:
   - Co się stało?
   - Jak to odtworzyć?
   - Jaki był oczekiwany wynik?
   - Załącz kod lub dane wejściowe.

---

## 💡 Proponowanie Zmian

1. Otwórz issue z opisem proponowanej zmiany.
2. Poczekaj na dyskusję i akceptację.
3. Stwórz fork repozytorium i gałąź (`feature/nazwa-zmiany`).
4. Wprowadź zmiany, przestrzegając standardów.

---

## 📝 Standardy Kodowania

- **Formatowanie**: Używamy `black` z domyślną konfiguracją.
- **Sortowanie importów**: `isort` z profilem `black`.
- **Lintowanie**: `flake8` z limitem 88 znaków.
- **Typowanie**: Dodawaj type hints dla wszystkich funkcji.

### Przykład:
```python
from typing import Optional, Dict, Any

def validate_equation(expr: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Waliduje wyrażenie matematyczne."""
    pass
🧪 Testy
Używamy pytest do testów jednostkowych i integracyjnych.

Testy znajdują się w katalogu tests/.

Przed commitem uruchom testy: pytest tests/

Struktura testów:
text
tests/
├── unit/
│   ├── test_parser.py
│   ├── test_validator.py
│   └── ...
├── integration/
│   ├── test_pipeline.py
│   └── ...
└── fixtures/
    └── sample_expressions.json
📦 Wymagania
Python 3.8+

Zainstalowane zależności: pip install -r requirements-dev.txt

🔄 Proces Pull Request
Zaktualizuj swoją gałąź do najnowszej wersji main.

Upewnij się, że wszystkie testy przechodzą.

Dodaj opisy zmian w CHANGELOG.md.

Wyślij Pull Request z opisem zmian i odnośnikiem do issue.

📧 Kontakt
W razie pytań: jbackk-lang@proton.me

Dziękujemy za Twój wkład! 🙌

text

---

## ✅ **KROK 3: Aktualizacja .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
*.whl

# Testy i coverage
.pytest_cache/
.coverage
htmlcov/
.tox/
*.log

# Środowisko
.env
venv/
env/
ENV/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Dokumentacja
docs/_build/

# Dane
*.csv
*.jsonl
*.db

# OS
.DS_Store
Thumbs.db
