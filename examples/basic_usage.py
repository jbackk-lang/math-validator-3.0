#!/usr/bin/env python3
"""
Przykład podstawowego użycia math-validator-2.0
"""

from math_validator import validate_equation

def main():
    # Przykład 1: Proste wyrażenie
    result = validate_equation("2 + 2 * 3")
    print(f"1. 2 + 2 * 3 → {result['status']}")
    print(f"   Błędy: {len(result['issues'])}")

    # Przykład 2: Błąd składniowy
    result = validate_equation("2 + * 3")
    print(f"2. 2 + * 3 → {result['status']}")

    # Przykład 3: Problem mylny
    result = validate_equation("1=1=1")
    print(f"3. 1=1=1 → {result['status']}")
    for issue in result['issues']:
        if issue['severity'] == 'misleading':
            print(f"   ⚠️ {issue['message']}")

if __name__ == "__main__":
    main()
