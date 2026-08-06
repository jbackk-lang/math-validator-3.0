#!/usr/bin/env python3
"""
Przykład analizy topologicznej z użyciem filtrów
"""

from math_validator import validate_equation

def main():
    # Wyrażenie z osobliwością
    expr = "1/(x-1)"

    result = validate_equation(
        expr,
        options={
            "topological": True,
            "singularity_detection": True
        }
    )

    print(f"Analiza topologiczna: {expr}")
    print(f"Status: {result['status']}")

    # Wyświetl filtry
    if 'filters' in result:
        for name, data in result['filters'].items():
            print(f"\n🔍 Filtr: {name}")
            print(f"   Status: {data.get('status', 'UNKNOWN')}")
            print(f"   Opis: {data.get('details', 'Brak')}")

if __name__ == "__main__":
    main()
