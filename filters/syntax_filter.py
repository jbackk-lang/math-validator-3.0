r"""
filters/syntax_filter.py — filtr składni

Poprawki v2:
  - Regex double_operator rozszerzony o wzorce z odstępem: "x + + y", "x - - y"
    (oryginał: r"[+\-*/]{2,}" nie łapał operatorów rozdzielonych spacją)
  - Dodane wykrywanie: leading/trailing operator (np. "x +", "+ x")
  - Zachowana kompatybilność wyjścia z oryginałem
"""

from core import ParsedExpr
import re

# Operatory podwójne BEZ odstępu: ++, --, +-, */, itp.
_RE_DOUBLE_OP_NOSPACE = re.compile(r"[+\-*/]{2,}")

# Operatory podwójne Z odstępem: "x + + y", "x - - 1"
# Usuwa ** (potęgowanie) przed sprawdzeniem
_RE_DOUBLE_OP_SPACE   = re.compile(r"(?<!\*)[+\-](?:\s+)[+\-]")

# Urwany operator na końcu: "x +", "x *"
_RE_TRAILING_OP       = re.compile(r"[+\-*/]\s*$")

# Urwany operator na początku (poza minus unarnym): "+ x", "* x"
_RE_LEADING_OP        = re.compile(r"^\s*[+*/]")


def run(p: ParsedExpr) -> dict:
    raw = p.raw

    # Usuń ** żeby nie wykrywać potęgowania jako podwójnego operatora
    raw_no_pow = raw.replace("**", "")

    balanced    = raw.count("(") == raw.count(")")
    empty_paren = "()" in raw

    # ── POPRAWKA: double_operator z i bez odstępu ─────────────────────────────
    double_op_nospace = bool(_RE_DOUBLE_OP_NOSPACE.search(raw_no_pow))
    double_op_space   = bool(_RE_DOUBLE_OP_SPACE.search(raw_no_pow))
    double_op         = double_op_nospace or double_op_space

    trailing_op = bool(_RE_TRAILING_OP.search(raw))
    leading_op  = bool(_RE_LEADING_OP.search(raw))

    issues = []
    if not balanced:    issues.append("unbalanced_parens")
    if double_op:       issues.append("double_operator")
    if empty_paren:     issues.append("empty_parens")
    if trailing_op:     issues.append("trailing_operator")
    if leading_op:      issues.append("leading_operator")
    if not p.ok:        issues.append(f"parse_error: {p.error}")

    return {
        "balanced_parens":  balanced,
        "double_operator":  double_op,
        "empty_parens":     empty_paren,
        "trailing_operator": trailing_op,
        "leading_operator": leading_op,
        "issues":           issues,
        "ok":               len(issues) == 0,
    }
