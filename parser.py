"""
parser.py — cienka warstwa nad core.parse().
Zachowany dla kompatybilności wstecznej z oryginalnym API.
"""

from core import parse, ParsedExpr


def parse_expr(expr: str) -> ParsedExpr:
    """Parsuje wyrażenie i zwraca ParsedExpr. Alias dla core.parse()."""
    return parse(expr)
