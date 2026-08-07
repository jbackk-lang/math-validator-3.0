"""
algebra.py — moduł root: deleguje do filters/algebra_filter.
Nie wywołuje sympify() samodzielnie.
"""
from core import parse
from filters.algebra_filter import run


def check_algebra(expr: str) -> dict:
    return run(parse(expr))
