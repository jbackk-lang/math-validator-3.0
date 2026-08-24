"""
plugins.py — Rozszerzalność / mechanizm wtyczek (v3)

Pozwala innym programistom dodawać własne filtry (funkcje/operatory/
reguły walidacji) bez modyfikacji rdzenia projektu.

Dwa sposoby rejestracji:

1) Dekorator, w kodzie, który się zaimportuje:

    from plugins import register_filter

    @register_filter("my_check")
    def run(parsed_expr):
        return {"status": "ok"}

2) Automatyczne ładowanie z katalogu — każdy plik *.py w katalogu
   wtyczek jest importowany; jeśli definiuje moduł-poziomową funkcję
   `run(p)`, zostaje zarejestrowany pod nazwą pliku:

    from plugins import load_plugins_from_dir
    load_plugins_from_dir("./my_plugins")

Zarejestrowane filtry są dostępne przez get_filters() i automatycznie
uwzględniane przez pipeline_v3.validate_all().
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Callable

_REGISTRY: dict[str, Callable] = {}


class PluginError(Exception):
    pass


def register_filter(name: str):
    """Dekorator: @register_filter("nazwa") nad funkcją run(p) -> dict."""
    if name in _REGISTRY:
        raise PluginError(f"filtr o nazwie {name!r} jest już zarejestrowany")

    def deco(fn: Callable) -> Callable:
        _REGISTRY[name] = fn
        return fn

    return deco


def unregister_filter(name: str) -> None:
    _REGISTRY.pop(name, None)


def get_filters() -> dict[str, Callable]:
    return dict(_REGISTRY)


def load_plugins_from_dir(directory: str) -> list[str]:
    """Importuje każdy *.py z katalogu; jeśli ma funkcję `run`, rejestruje
    ją pod nazwą pliku (bez rozszerzenia). Zwraca listę nazw załadowanych wtyczek."""
    loaded = []
    d = Path(directory)
    if not d.is_dir():
        raise PluginError(f"katalog wtyczek nie istnieje: {directory}")

    for path in sorted(d.glob("*.py")):
        if path.name.startswith("_"):
            continue
        mod_name = f"_math_validator_plugin_{path.stem}"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise PluginError(f"błąd ładowania wtyczki {path.name}: {e}")

        run_fn = getattr(module, "run", None)
        if callable(run_fn) and path.stem not in _REGISTRY:
            _REGISTRY[path.stem] = run_fn
            loaded.append(path.stem)

    return loaded


def run_all_plugins(parsed_expr) -> dict:
    """Uruchamia wszystkie zarejestrowane wtyczki na sparsowanym wyrażeniu."""
    results = {}
    for name, fn in _REGISTRY.items():
        try:
            results[name] = fn(parsed_expr)
        except Exception as e:
            results[name] = {"status": "error", "message": f"wtyczka {name!r} zgłosiła wyjątek: {e}"}
    return results
