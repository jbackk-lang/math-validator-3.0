#!/usr/bin/env python3
"""
Przykład analizy wymiarowej i algebry liniowej z użyciem modułów v3.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from units import analyze_units
from linalg import validate_matrix_expression


def main():
    # Analiza wymiarowa: droga = prędkość * czas + 1/2 * przyspieszenie * czas^2
    r = analyze_units("v*t + 0.5*a*t**2", {"v": "m/s", "t": "s", "a": "m/s**2"})
    print("Analiza wymiarowa: v*t + 0.5*a*t**2")
    print(f"  status: {r['status']}, wymiar wyniku: {r.get('result_dimension')}")

    # Niepoprawne wymiarowo dodawanie
    r = analyze_units("x + t", {"x": "m", "t": "s"})
    print("\nAnaliza wymiarowa: x + t (metry + sekundy)")
    print(f"  status: {r['status']}, komunikat: {r.get('message')}")

    # Walidacja mnożenia macierzy
    r = validate_matrix_expression("Matrix([[1,2,3],[4,5,6]]) * Matrix([[1,2],[3,4]])")
    print("\nMnożenie macierzy 2x3 * 2x2:")
    print(f"  status: {r['status']}, komunikat: {r.get('message')}")


if __name__ == "__main__":
    main()
