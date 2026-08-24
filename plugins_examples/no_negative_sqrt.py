"""
plugins_examples/no_negative_sqrt.py — przykładowa wtyczka.

Ładowana przez:
    import plugins
    plugins.load_plugins_from_dir("plugins_examples")

Każdy plik z funkcją run(p) na poziomie modułu staje się filtrem
dostępnym w pipeline_v3.validate_all() pod kluczem "plugins" ->
"no_negative_sqrt", bez modyfikowania rdzenia projektu.
"""
from sympy import Pow, Rational


def run(p) -> dict:
    """Ostrzega, jeśli wyrażenie zawiera sqrt() z jawnie ujemnym argumentem liczbowym."""
    # sym_raw (nieewaluowane) — bo sympify(evaluate=True) już uprościłby
    # sqrt(-4) do 2*I, zanim zdążylibyśmy go tu wykryć.
    sym = getattr(p, "sym_raw", None) or getattr(p, "sym", None)
    if sym is None:
        return {"status": "skip"}

    issues = []
    for node in sym.atoms(Pow):
        base, exp = node.args
        if exp == Rational(1, 2) and base.is_number and base.is_negative:
            issues.append(f"sqrt({base}) — pierwiastek z liczby ujemnej, wynik zespolony")

    return {"status": "warning" if issues else "ok", "issues": issues}
