"""
ambiguity.py — Zarządzanie Niejednoznacznością (v3)

Wykrywa zapisy, które są składniowo poprawne, ale mają więcej niż jedną
sensowną interpretację matematyczną (np. `a/b*c`, `a^b^c`, `-a^b`,
`1/2x`), i proponuje jednoznaczny zapis z nawiasami dla każdej możliwej
interpretacji. Priorytety operatorów są konfigurowalne przez
`PrecedenceConfig`, więc użytkownik może zdefiniować własną domyślną
interpretację (np. potraktować mnożenie niejawne `2x` jako silniejsze
niż dzielenie `/`, tak jak robi to część kalkulatorów naukowych).

Użycie:
    from ambiguity import find_ambiguities, PrecedenceConfig
    find_ambiguities("a/b*c")
    find_ambiguities("1/2x", config=PrecedenceConfig(implicit_mult_binds_tighter=True))
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PrecedenceConfig:
    # Czy niejawne mnożenie (np. "2x") wiąże silniej niż jawne "/" i "*"
    # (konwencja spotykana np. w niektórych kalkulatorach: 1/2x == 1/(2x))
    implicit_mult_binds_tighter: bool = False
    # Łączność potęgowania: 'right' (standard matematyczny, a^b^c = a^(b^c))
    # lub 'left' (konwencja niektórych języków programowania)
    power_associativity: str = "right"


DEFAULT_CONFIG = PrecedenceConfig()


@dataclass
class Ambiguity:
    kind: str
    span: tuple[int, int]
    snippet: str
    message: str
    interpretations: dict  # {"standard": "...", "alt": "..."}
    resolved: str  # zapis zgodny z podanym PrecedenceConfig


def _find_chained_division(expr: str) -> list[Ambiguity]:
    out = []
    # a/b/c  lub  a/b*c  (bez nawiasów rozstrzygających)
    for m in re.finditer(r"([A-Za-z0-9_.]+)\s*/\s*([A-Za-z0-9_.]+)\s*([*/])\s*([A-Za-z0-9_.]+)", expr):
        a, b, op, c = m.groups()
        left_to_right = f"({a}/{b}){op}{c}"  # standardowa reguła: lewostronna łączność
        out.append(Ambiguity(
            kind="chained_division",
            span=m.span(),
            snippet=m.group(0),
            message=(
                f"'{m.group(0)}' bywa czytane jako '{a}/({b}{op}{c})' przez ludzi, "
                f"ale standardowa reguła lewostronnej łączności daje '{left_to_right}'."
            ),
            interpretations={
                "left_to_right (standard)": left_to_right,
                "human_reading (błędne wg standardu)": f"{a}/({b}{op}{c})",
            },
            resolved=left_to_right,
        ))
    return out


def _find_chained_power(expr: str, config: PrecedenceConfig) -> list[Ambiguity]:
    out = []
    for m in re.finditer(r"([A-Za-z0-9_.]+)\s*\^\s*([A-Za-z0-9_.]+)\s*\^\s*([A-Za-z0-9_.]+)", expr):
        a, b, c = m.groups()
        right = f"{a}^({b}^{c})"
        left = f"({a}^{b})^{c}"
        resolved = right if config.power_associativity == "right" else left
        out.append(Ambiguity(
            kind="chained_power",
            span=m.span(),
            snippet=m.group(0),
            message=(
                f"'{m.group(0)}' jest niejednoznaczne: matematyczna konwencja to "
                f"prawostronna łączność ('{right}'), ale niektóre systemy liczą lewostronnie ('{left}')."
            ),
            interpretations={"right_assoc (standard matematyczny)": right, "left_assoc": left},
            resolved=resolved,
        ))
    return out


def _find_unary_minus_before_power(expr: str) -> list[Ambiguity]:
    out = []
    for m in re.finditer(r"(?<![A-Za-z0-9_)])-\s*([A-Za-z0-9_.]+)\s*\^\s*([A-Za-z0-9_.]+)", expr):
        base, exp = m.groups()
        std = f"-({base}^{exp})"   # standard: potęgowanie wiąże silniej niż unarny minus
        alt = f"(-{base})^{exp}"
        out.append(Ambiguity(
            kind="unary_minus_before_power",
            span=m.span(),
            snippet=m.group(0),
            message=(
                f"'-{base}^{exp}' jest często mylnie czytane jako '{alt}', "
                f"ale standardowa konwencja (zgodna np. z Python/most CAS) to '{std}'."
            ),
            interpretations={"standard": std, "alt (błędna, ale częsta)": alt},
            resolved=std,
        ))
    return out


def _find_implicit_mult_vs_division(expr: str, config: PrecedenceConfig) -> list[Ambiguity]:
    out = []
    # np. "1/2x" — dzielenie po którym następuje niejawne mnożenie
    for m in re.finditer(r"([A-Za-z0-9_.]+)\s*/\s*([0-9]+)([A-Za-z][A-Za-z0-9_]*)\b", expr):
        a, num, var = m.groups()
        standard = f"({a}/{num})*{var}"       # a/2x == (a/2)*x, reguła lewostronna
        alt = f"{a}/({num}*{var})"            # a/2x == a/(2x), konwencja "silnego" niejawnego mnożenia
        resolved = alt if config.implicit_mult_binds_tighter else standard
        out.append(Ambiguity(
            kind="implicit_mult_vs_division",
            span=m.span(),
            snippet=m.group(0),
            message=(
                f"'{m.group(0)}' jest klasycznie niejednoznaczne: standard token-po-tokenie daje "
                f"'{standard}', ale konwencja 'silnego' niejawnego mnożenia daje '{alt}'."
            ),
            interpretations={"standard (lewo-prawo)": standard, "implicit_mult_tighter": alt},
            resolved=resolved,
        ))
    return out


def find_ambiguities(expr: str, config: PrecedenceConfig = DEFAULT_CONFIG) -> dict:
    ambiguities: list[Ambiguity] = []
    ambiguities += _find_chained_division(expr)
    ambiguities += _find_chained_power(expr, config)
    ambiguities += _find_unary_minus_before_power(expr)
    ambiguities += _find_implicit_mult_vs_division(expr, config)

    return {
        "status": "ok",
        "expression": expr,
        "ambiguity_count": len(ambiguities),
        "ambiguities": [
            {
                "kind": a.kind,
                "snippet": a.snippet,
                "span": a.span,
                "message": a.message,
                "interpretations": a.interpretations,
                "suggested_parenthesization": a.resolved,
            }
            for a in ambiguities
        ],
        "config": {
            "implicit_mult_binds_tighter": config.implicit_mult_binds_tighter,
            "power_associativity": config.power_associativity,
        },
    }
