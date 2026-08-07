#!/usr/bin/env python3
"""
cli.py — Interfejs Linii Poleceń dla math-validator v3.

Przykłady:
    python cli.py "2+2*3"
    python cli.py "x/x" --pretty
    python cli.py "(A ∧ B) → C" --formula
    python cli.py "Matrix([[1,2]]) * Matrix([[1,2]])" --matrix
    python cli.py "v*t" --units v=m/s --units t=s
    python cli.py "2*x + 3*x" --normalize-only
    echo "2+2*3" | python cli.py -

W CI/CD:
    python cli.py "$EXPR" --fail-on-issues   # exit code 1 jeśli status != ok

Po zainstalowaniu pakietu (patrz pyproject.toml) dostępne jako:
    math-validator "2+2*3"
"""
from __future__ import annotations

import argparse
import json
import sys

from pipeline_v3 import validate_all
from ambiguity import PrecedenceConfig
from sympy_bridge import SymPyBridge


def _parse_units(pairs: list[str]) -> dict:
    units = {}
    for p in pairs or []:
        if "=" not in p:
            raise argparse.ArgumentTypeError(f"oczekiwano formatu zmienna=jednostka, otrzymano {p!r}")
        name, unit = p.split("=", 1)
        units[name.strip()] = unit.strip()
    return units


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="math-validator",
        description="Topologiczny walidator równań matematycznych — CLI v3.",
    )
    p.add_argument("expression", help="wyrażenie do zwalidowania, lub '-' aby czytać ze stdin")
    p.add_argument("--formula", action="store_true", help="traktuj wejście jako formułę logiki zdaniowej")
    p.add_argument("--matrix", action="store_true", help="traktuj wejście jako wyrażenie macierzowe")
    p.add_argument("--units", action="append", metavar="ZMIENNA=JEDNOSTKA",
                    help="przypisz jednostkę zmiennej dla analizy wymiarowej (można powtórzyć)")
    p.add_argument("--normalize-only", action="store_true", help="tylko uprość/znormalizuj wyrażenie")
    p.add_argument("--solve", metavar="ZMIENNA", help="rozwiąż wyrażenie=0 względem podanej zmiennej")
    p.add_argument("--diff", metavar="ZMIENNA", help="policz pochodną po podanej zmiennej")
    p.add_argument("--latex", action="store_true", help="wypisz wyrażenie w LaTeX-u")
    p.add_argument("--implicit-mult-tighter", action="store_true",
                    help="konfiguracja niejednoznaczności: niejawne mnożenie wiąże silniej niż /")
    p.add_argument("--power-left-assoc", action="store_true",
                    help="konfiguracja niejednoznaczności: a^b^c = (a^b)^c zamiast a^(b^c)")
    p.add_argument("--pretty", action="store_true", help="czytelne wcięcia w JSON")
    p.add_argument("--fail-on-issues", action="store_true",
                    help="exit code 1 jeśli status != 'ok' (przydatne w CI/CD)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    expr = sys.stdin.read().strip() if args.expression == "-" else args.expression

    if args.normalize_only:
        from normalize import normalize_expression
        output = normalize_expression(expr)
    elif args.solve:
        output = SymPyBridge(expr).solve(args.solve)
    elif args.diff:
        output = SymPyBridge(expr).diff(args.diff)
    elif args.latex:
        output = SymPyBridge(expr).latex()
    else:
        units = _parse_units(args.units)
        config = PrecedenceConfig(
            implicit_mult_binds_tighter=args.implicit_mult_tighter,
            power_associativity="left" if args.power_left_assoc else "right",
        )
        output = validate_all(
            expr,
            formula=args.formula,
            units=units or None,
            matrix=args.matrix,
            precedence_config=config,
        )

    indent = 2 if args.pretty else None
    print(json.dumps(output, indent=indent, ensure_ascii=False))

    if args.fail_on_issues and output.get("status") not in ("ok", None):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
