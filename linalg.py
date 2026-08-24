"""
linalg.py — Moduł Algebry Liniowej (v3)

Waliduje wymiary macierzy/wektorów przed wykonaniem operacji: mnożenie,
dodawanie, odwracanie, wyznacznik — zanim w ogóle spróbujemy policzyć
wynik. Akceptuje wyrażenia w składni sympy, np.:

    "Matrix([[1,2],[3,4]]) * Matrix([[1],[0]])"
    "Matrix([[1,2,3],[4,5,6]]) + Matrix([[1,1],[1,1]])"

Zwraca precyzyjny komunikat błędu (np. "nie można pomnożyć macierzy
2x3 przez 2x2 — liczba kolumn lewej (3) musi równać się liczbie
wierszy prawej (2)") zamiast surowego wyjątku sympy.
"""
from __future__ import annotations

from sympy import sympify, MatrixSymbol
from sympy.matrices import Matrix, ImmutableMatrix
from sympy.matrices.expressions import MatMul, MatAdd, MatrixExpr, Inverse, Determinant, Transpose


def _shape(m) -> tuple[int, int]:
    if hasattr(m, "shape"):
        return tuple(m.shape)
    raise TypeError(f"nie jest macierzą: {m}")


def _walk(expr, issues: list, notes: list):
    args = getattr(expr, "args", ())

    if isinstance(expr, MatMul):
        mats = [a for a in args if hasattr(a, "shape")]
        for left, right in zip(mats, mats[1:]):
            lr, lc = _shape(left)
            rr, rc = _shape(right)
            if lc != rr:
                issues.append(
                    f"Niezgodność wymiarów mnożenia: nie można pomnożyć macierzy "
                    f"{lr}x{lc} przez {rr}x{rc} — liczba kolumn lewej ({lc}) musi "
                    f"równać się liczbie wierszy prawej ({rr})."
                )
            else:
                notes.append(f"OK: mnożenie {lr}x{lc} * {rr}x{rc} -> wynik {lr}x{rc}")

    if isinstance(expr, MatAdd):
        mats = [a for a in args if hasattr(a, "shape")]
        if mats:
            first_shape = _shape(mats[0])
            for m in mats[1:]:
                s = _shape(m)
                if s != first_shape:
                    issues.append(
                        f"Niezgodność wymiarów dodawania: macierz {first_shape[0]}x{first_shape[1]} "
                        f"i macierz {s[0]}x{s[1]} muszą mieć te same wymiary."
                    )

    if isinstance(expr, Inverse):
        (m,) = args
        r, c = _shape(m)
        if r != c:
            issues.append(f"Nie można odwrócić macierzy niekwadratowej {r}x{c}.")
        else:
            try:
                det = Matrix(m).det() if not isinstance(m, MatrixSymbol) else None
                if det is not None and det == 0:
                    issues.append(f"Macierz {r}x{r} jest osobliwa (det = 0) — nie ma odwrotności.")
            except Exception:
                pass

    if isinstance(expr, Determinant):
        (m,) = args
        r, c = _shape(m)
        if r != c:
            issues.append(f"Wyznacznik zdefiniowany tylko dla macierzy kwadratowych, otrzymano {r}x{c}.")

    for a in args:
        _walk(a, issues, notes)


import re as _re

_SIZE_MISMATCH_RE = _re.compile(
    r"Matrix size mismatch:\s*\((\d+),\s*(\d+)\)\s*([*+])\s*\((\d+),\s*(\d+)\)"
)


def validate_matrix_expression(expr_str: str) -> dict:
    try:
        expr = sympify(expr_str)
    except Exception as e:
        m = _SIZE_MISMATCH_RE.search(str(e))
        if m:
            ar, ac, op, br, bc = m.groups()
            ar, ac, br, bc = int(ar), int(ac), int(br), int(bc)
            if op == "*":
                msg = (
                    f"Niezgodność wymiarów mnożenia: nie można pomnożyć macierzy "
                    f"{ar}x{ac} przez {br}x{bc} — liczba kolumn lewej ({ac}) musi "
                    f"równać się liczbie wierszy prawej ({br})."
                )
            else:
                msg = (
                    f"Niezgodność wymiarów dodawania: macierz {ar}x{ac} i macierz "
                    f"{br}x{bc} muszą mieć te same wymiary."
                )
            return {"status": "error", "message": msg, "issues": [msg], "notes": [], "result_shape": None}
        return {"status": "error", "message": f"błąd parsowania: {e}"}

    issues: list[str] = []
    notes: list[str] = []
    _walk(expr, issues, notes)

    result_shape = None
    if hasattr(expr, "shape"):
        try:
            result_shape = tuple(expr.shape)
        except Exception:
            result_shape = None

    return {
        "status": "error" if issues else "ok",
        "expression": expr_str,
        "issues": issues,
        "notes": notes,
        "result_shape": result_shape,
    }


def check_multiplication_compatible(shape_a: tuple[int, int], shape_b: tuple[int, int]) -> dict:
    ar, ac = shape_a
    br, bc = shape_b
    ok = ac == br
    return {
        "compatible": ok,
        "result_shape": (ar, bc) if ok else None,
        "message": (
            f"OK: {ar}x{ac} * {br}x{bc} -> {ar}x{bc}" if ok else
            f"Niezgodność: kolumny lewej ({ac}) != wiersze prawej ({br})"
        ),
    }


def check_addition_compatible(shape_a: tuple[int, int], shape_b: tuple[int, int]) -> dict:
    ok = shape_a == shape_b
    return {
        "compatible": ok,
        "result_shape": shape_a if ok else None,
        "message": "OK: wymiary identyczne" if ok else f"Niezgodność: {shape_a} != {shape_b}",
    }
