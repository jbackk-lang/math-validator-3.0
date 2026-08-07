"""
units.py — Weryfikacja Jednostek (Wymiarów) — v3

Sprawdza, czy wyrażenie matematyczne jest spójne wymiarowo: np. nie
pozwala dodać metrów do sekund, ale pozwala pomnożyć metry przez
metry^-1 (bezwymiarowe), sinusa liczyć tylko z argumentu bezwymiarowego
itd. Nie wymaga zewnętrznych zależności poza sympy.

Użycie:
    from units import analyze_units
    analyze_units("v*t + 0.5*a*t**2", {"v": "m/s", "t": "s", "a": "m/s**2"})

Wspiera notację jednostek złożonych w samym unit-stringu, np. "m/s**2",
"kg*m/s**2", "1" (bezwymiarowe).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sympy import (
    Symbol, Add, Mul, Pow, sympify, Function, Number, S,
)

BASE_DIMS = ("L", "M", "T", "I", "Theta", "N", "J")  # długość, masa, czas,
# natężenie prądu, temperatura, ilość materii, światłość


@dataclass(frozen=True)
class Dim:
    """Wektor wykładników wymiarowych (SI)."""
    L: int = 0
    M: int = 0
    T: int = 0
    I: int = 0
    Theta: int = 0
    N: int = 0
    J: int = 0

    def __mul__(self, other: "Dim") -> "Dim":
        return Dim(**{d: getattr(self, d) + getattr(other, d) for d in BASE_DIMS})

    def __truediv__(self, other: "Dim") -> "Dim":
        return Dim(**{d: getattr(self, d) - getattr(other, d) for d in BASE_DIMS})

    def pow(self, n) -> "Dim":
        return Dim(**{d: getattr(self, d) * n for d in BASE_DIMS})

    @property
    def is_dimensionless(self) -> bool:
        return all(getattr(self, d) == 0 for d in BASE_DIMS)

    def __str__(self) -> str:
        if self.is_dimensionless:
            return "1 (bezwymiarowe)"
        parts = []
        symbol_map = {"L": "m", "M": "kg", "T": "s", "I": "A", "Theta": "K", "N": "mol", "J": "cd"}
        for d in BASE_DIMS:
            exp = getattr(self, d)
            if exp != 0:
                parts.append(symbol_map[d] if exp == 1 else f"{symbol_map[d]}^{exp}")
        return "*".join(parts)


# ── Tablica jednostek bazowych i pochodnych SI ───────────────────────────
_BASE_UNITS = {
    "m": Dim(L=1), "km": Dim(L=1), "cm": Dim(L=1), "mm": Dim(L=1),
    "s": Dim(T=1), "min": Dim(T=1), "h": Dim(T=1), "ms": Dim(T=1),
    "kg": Dim(M=1), "g": Dim(M=1),
    "A": Dim(I=1),
    "K": Dim(Theta=1),
    "mol": Dim(N=1),
    "cd": Dim(J=1),
    "rad": Dim(),  # kąt płaski — bezwymiarowy w SI
}
_DERIVED_UNITS = {
    "N": Dim(M=1, L=1, T=-2),        # Newton
    "J": Dim(M=1, L=2, T=-2),        # Julia (energia)
    "W": Dim(M=1, L=2, T=-3),        # Wat
    "Pa": Dim(M=1, L=-1, T=-2),      # Paskal
    "Hz": Dim(T=-1),                 # Herz
    "V": Dim(M=1, L=2, T=-3, I=-1),  # Volt
    "C": Dim(T=1, I=1),              # Coulomb
    "Ohm": Dim(M=1, L=2, T=-3, I=-2),
}
UNIT_TABLE = {**_BASE_UNITS, **_DERIVED_UNITS}

_DIMENSIONLESS_FUNCS = {"sin", "cos", "tan", "cot", "exp", "log", "ln", "asin", "acos", "atan"}


class DimensionError(Exception):
    def __init__(self, message: str, node=None):
        super().__init__(message)
        self.message = message
        self.node = node


def parse_unit_string(unit_str: str) -> Dim:
    """Parsuje string jednostki złożonej, np. 'm/s**2', 'kg*m/s**2', '1'."""
    unit_str = unit_str.strip()
    if unit_str in ("", "1", "-"):
        return Dim()

    unit_symbols = {name: Symbol(name) for name in UNIT_TABLE}
    try:
        expr = sympify(unit_str, locals=unit_symbols)
    except Exception as e:
        raise DimensionError(f"nie można sparsować jednostki {unit_str!r}: {e}")

    return _dim_of_unit_expr(expr)


def _dim_of_unit_expr(expr) -> Dim:
    if isinstance(expr, Symbol):
        if expr.name not in UNIT_TABLE:
            raise DimensionError(f"nieznana jednostka: {expr.name!r}")
        return UNIT_TABLE[expr.name]
    if isinstance(expr, Number):
        return Dim()
    if isinstance(expr, Mul):
        d = Dim()
        for arg in expr.args:
            d = d * _dim_of_unit_expr(arg)
        return d
    if isinstance(expr, Pow):
        base, exp = expr.args
        if not exp.is_number:
            raise DimensionError(f"wykładnik jednostki musi być liczbą: {expr}")
        return _dim_of_unit_expr(base).pow(exp)
    raise DimensionError(f"nieobsługiwana struktura jednostki: {expr}")


def _dim_of(expr, var_dims: dict[str, Dim]) -> Dim:
    """Rekurencyjnie oblicza wymiar poddrzewa wyrażenia sympy."""
    if isinstance(expr, Symbol):
        if expr.name in var_dims:
            return var_dims[expr.name]
        # zmienna bez jawnie podanej jednostki traktowana jako bezwymiarowa
        return Dim()

    if isinstance(expr, Number) or expr.is_number:
        return Dim()

    if isinstance(expr, Add):
        dims = [_dim_of(a, var_dims) for a in expr.args]
        first = dims[0]
        for d, term in zip(dims[1:], expr.args[1:]):
            if d != first:
                raise DimensionError(
                    f"niespójność wymiarowa w sumie: składnik {expr.args[0]} ma wymiar "
                    f"[{first}], a składnik {term} ma wymiar [{d}]",
                    node=expr,
                )
        return first

    if isinstance(expr, Mul):
        d = Dim()
        for a in expr.args:
            d = d * _dim_of(a, var_dims)
        return d

    if isinstance(expr, Pow):
        base, exp = expr.args
        base_dim = _dim_of(base, var_dims)
        if exp.is_number:
            return base_dim.pow(exp)
        if not base_dim.is_dimensionless:
            raise DimensionError(
                f"wykładnik niebędący liczbą przy podstawie wymiarowej: {expr}", node=expr
            )
        return Dim()

    if isinstance(expr, Function):
        fname = expr.func.__name__
        arg_dims = [_dim_of(a, var_dims) for a in expr.args]
        if fname.lower() in _DIMENSIONLESS_FUNCS:
            for ad, arg in zip(arg_dims, expr.args):
                if not ad.is_dimensionless:
                    raise DimensionError(
                        f"funkcja {fname}() wymaga argumentu bezwymiarowego, "
                        f"a {arg} ma wymiar [{ad}]", node=expr
                    )
            return Dim()  # sin/cos/... zwracają wartość bezwymiarową
        # nieznana funkcja: zakładamy, że przenosi wymiar pierwszego argumentu
        return arg_dims[0] if arg_dims else Dim()

    # domyślnie: potraktuj jako bezwymiarowe (np. stałe symboliczne pi, E)
    return Dim()


def analyze_units(expr_str: str, units: dict[str, str]) -> dict:
    """
    expr_str : wyrażenie matematyczne, np. "v*t + 0.5*a*t**2"
    units    : mapowanie nazwa_zmiennej -> jednostka (string), np.
               {"v": "m/s", "t": "s", "a": "m/s**2"}
    """
    try:
        var_dims = {name: parse_unit_string(u) for name, u in units.items()}
    except DimensionError as e:
        return {"status": "error", "message": str(e), "stage": "unit_parsing"}

    try:
        expr = sympify(expr_str)
    except Exception as e:
        return {"status": "error", "message": f"błąd parsowania wyrażenia: {e}", "stage": "expr_parsing"}

    try:
        result_dim = _dim_of(expr, var_dims)
    except DimensionError as e:
        return {
            "status": "error",
            "message": e.message,
            "stage": "dimensional_check",
            "offending_subexpression": str(e.node) if e.node is not None else None,
        }

    return {
        "status": "ok",
        "expression": expr_str,
        "result_dimension": str(result_dim),
        "is_dimensionless": result_dim.is_dimensionless,
        "variable_units": units,
    }
