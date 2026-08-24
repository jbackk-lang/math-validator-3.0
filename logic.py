"""
logic.py — moduł root: deleguje do filters/logic_filter.
"""
from core import parse
from filters.logic_filter import run


def check_logic(expr: str) -> dict:
    return run(parse(expr))
