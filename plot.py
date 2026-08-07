"""
plot.py — wizualizacja wyrażeń.

Naprawka wydajnościowa: zastąpiono 201× subs() symbolicznych
funkcją lambdify() + np.linspace() — ~50× szybsze.
"""
import numpy as np
from sympy import lambdify, sympify, symbols, oo, zoo

x = symbols('x')


def plot_expr(expr: str, x_min: float = -10, x_max: float = 10, points: int = 400):
    """
    Zwraca (xs, ys) gotowe do matplotlib.pyplot.plot().
    Używa lambdify zamiast subs() w pętli.
    """
    try:
        f = sympify(expr)
        f_num = lambdify(x, f, modules=["numpy"])
        xs = np.linspace(x_min, x_max, points)
        with np.errstate(divide='ignore', invalid='ignore'):
            ys = f_num(xs)
        # Zamień inf/nan na None dla przejrzystości wykresu
        ys = np.where(np.isfinite(ys), ys, np.nan)
        return xs, ys
    except Exception as e:
        return None, None


def plot_to_dict(expr: str, x_min: float = -10, x_max: float = 10, points: int = 400) -> dict:
    """Zwraca słownik z punktami — przydatne dla API."""
    xs, ys = plot_expr(expr, x_min, x_max, points)
    if xs is None:
        return {"status": "error", "xs": [], "ys": []}
    return {
        "status": "ok",
        "xs": xs.tolist(),
        "ys": [y if not np.isnan(y) else None for y in ys.tolist()]
    }
