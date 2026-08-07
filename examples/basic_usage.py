#!/usr/bin/env python3
"""
Przykład podstawowego użycia math-validator (v3).
Realne API: pipeline_v3.validate_all (patrz README / CHANGELOG_v3.md).
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline_v3 import validate_all


def main():
    # Przykład 1: proste wyrażenie
    result = validate_all("2 + 2 * 3")
    print(f"1. 2 + 2 * 3 -> status: {result['status']}")

    # Przykład 2: błąd składniowy (brakujący nawias)
    result = validate_all("sin(x + 1")
    print(f"2. sin(x + 1 -> status: {result['status']}")
    for d in result["syntax_diagnostics"]["diagnostics"]:
        print(f"   błąd w pozycji {d['position']}: {d['message']} ({d['hint']})")

    # Przykład 3: normalizacja z ostrzeżeniem o utraconej dziedzinie
    result = validate_all("(x**2 - 1)/(x-1)")
    print(f"3. (x**2-1)/(x-1) -> uproszczone: {result['normalize']['normalized']}")
    for c in result["normalize"]["caveats"]:
        print(f"   uwaga: {c}")


if __name__ == "__main__":
    main()
