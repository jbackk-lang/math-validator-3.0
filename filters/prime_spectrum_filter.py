"""
prime_spectrum_filter.py — analizuje widmo liczb pierwszych
związane z wyrażeniem typu N (liczba naturalna).

Idea:
- jeśli wyrażenie upraszcza się do liczby całkowitej N > 2
- bierzemy liczby pierwsze p ≤ N**(1/3)
- liczymy:
  - listę pierwszych
  - różnice między kolejnymi (gaps)
  - stosunki p_{n+1} / p_n
  - klasyfikację widma (quasi 1/f vs „nieregularne") WZGLĘDEM MODELU
    ZEROWEGO (patrz niżej — to jest naprawa, nie oryginalna wersja)

POPRAWKA (naprawiono ungruntowany próg + usunięto fałszywe twierdzenie
o związku z TIMDR):

Oryginalna wersja etykietowała wynik "log_spiral_1_over_f" — z dopisaną
notatką "widmo zgodne z logarytmiczną spiralą / 1/f (Λ–τ–ρ/TIMDR)" —
gdy średnia znormalizowana różnica między gaps i log(x+1) była < 0.25.
Próg 0.25 nie miał żadnego uzasadnienia statystycznego (brak modelu
zerowego), a twierdzenie o zgodności z TIMDR Λ–τ–ρ nie było niczym
poparte poza samą nazwą etykiety.

Zweryfikowano to (protokół zaproponowany i wykonany w sesji, patrz skill
timdr-signal-framework §17 case study 4 / §18 punkt 1):

1. Zbudowano model zerowy: 1000 losowych rosnących ciągów całkowitych o
   tej samej długości i podobnym zakresie kroków co obserwowane gaps.
2. Próg ustalono jako 5. percentyl rozkładu metryki (diff) z modelu
   zerowego — czyli z definicji tylko ~5% losowych ciągów miałoby
   diff poniżej progu.
3. Sprawdzono realne liczby pierwsze względem tego progu na dwa sposoby:
   - operacyjnie (prefiksy od 2 do N^(1/3) dla wielu N — dokładnie tak,
     jak filtr jest faktycznie używany): 21% oznaczonych jako
     "log_spiral_1_over_f" dla małych/średnich N, ale ZERO dla N > 2e6
     (diff realnych gaps rośnie do ~0.45–0.68, znacznie ponad próg —
     te próbki są zagnieżdżone/skorelowane, nie niezależne, więc ten
     wynik sam w sobie nie jest rozstrzygający).
   - niezależnie: nienachodzące na siebie okna o długości L wzdłuż
     78498 prawdziwych liczb pierwszych do 10^6 (prawdziwie
     niezależne(ish) próbki struktury gaps, nie tylko od N=2):
     L=5 → 2.73%, L=7 → 2.10%, L=10 → 1.17%, L=15 → 0.31% oznaczonych
     "log_spiral_1_over_f" — WSZYSTKIE PONIŻEJ oczekiwanych ~5% z modelu
     zerowego, malejąco z długością okna.
4. Wniosek: prawdziwe liczby pierwsze NIE przekraczają progu istotnie
   częściej niż losowe ciągi — jeśli już, to rzadziej. Filtr nie
   wykrywa niczego specyficznego dla liczb pierwszych w tym teście.
   Zgodnie z regułą zaproponowaną przy tej naprawie ("jeśli nie →
   etykieta powinna zniknąć albo być oznaczona jako czysto
   heurystyczna"): **usunięto twierdzenie o związku z TIMDR Λ–τ–ρ**.
   Klasyfikacja została, bo jest teraz przynajmniej statystycznie
   zdefiniowana (względem modelu zerowego), ale notatka jawnie mówi, że
   to wynik jednego wąskiego testu, nie potwierdzona własność liczb
   pierwszych, i nie ma nic wspólnego z TIMDR.
"""

from core import ParsedExpr
from sympy import primerange
from math import log

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False


def _diff_metric(gaps):
    """Średnia znormalizowana różnica między gaps i log(x+1). Mniejsza
    wartość = ciąg "bliżej" gładkiej krzywej logarytmicznej. Wydzielona
    z klasyfikacji, żeby użyć tej samej definicji i na realnych gaps, i
    na modelu zerowym poniżej."""
    if len(gaps) < 3:
        return None

    xs = list(range(1, len(gaps) + 1))
    logs = [log(x + 1) for x in xs]

    def norm(vs):
        vmin, vmax = min(vs), max(vs)
        if vmax == vmin:
            return [0.0 for _ in vs]
        return [(v - vmin) / (vmax - vmin) for v in vs]

    g_n = norm(gaps)
    l_n = norm(logs)

    return sum(abs(a - b) for a, b in zip(g_n, l_n)) / len(g_n)


def _null_model_threshold(gap_count, step_max, n_trials=1000, seed=0, pct=5):
    """Rozkład _diff_metric() na `n_trials` losowych rosnących ciągach
    całkowitych o długości `gap_count` i krokach jednostajnych w
    [1, step_max] (step_max dobrany z obserwowanych gaps, żeby model
    zerowy miał podobny zakres kroków co realne dane).

    Zwraca próg = `pct`-ty percentyl tego rozkładu (dolny ogon — mniejszy
    diff = "lepsze dopasowanie" do log-spirali). Bez numpy zwraca None
    (klasyfikacja wtedy spada do "irregular" — brak modelu zerowego to
    udokumentowane ograniczenie, nie cichy fallback do starego progu)."""
    if not _HAS_NUMPY:
        return None

    rng = np.random.default_rng(seed)
    step_max = max(int(step_max), 1)
    diffs = []
    for _ in range(n_trials):
        steps = rng.integers(1, step_max + 1, size=gap_count)
        d = _diff_metric(list(steps))
        if d is not None:
            diffs.append(d)

    if not diffs:
        return None
    return float(np.percentile(diffs, pct))


def _classify_spectrum(gaps):
    """
    Klasyfikacja względem modelu zerowego (patrz nagłówek pliku).
    Zwraca (spectrum_type, diff, threshold) — threshold=None jeśli
    numpy niedostępne lub model zerowy nie dał się policzyć.
    """
    if len(gaps) < 3:
        return "too_few_primes", None, None

    diff = _diff_metric(gaps)
    threshold = _null_model_threshold(len(gaps), max(gaps))

    if threshold is None:
        return "irregular", diff, None

    if diff < threshold:
        return "log_spiral_1_over_f", diff, threshold
    return "irregular", diff, threshold


def run(p: ParsedExpr) -> dict:
    if p.error:
        return {
            "status": "error",
            "message": p.error,
            "notes": ["nie można przeanalizować widma liczb pierwszych — błąd parse()"]
        }

    if not (p.sym is not None and p.sym.is_integer):
        return {
            "status": "skip",
            "message": "wyrażenie nie jest liczbą całkowitą — pomijam prime_spectrum",
            "notes": []
        }

    try:
        N = int(p.sym)
    except Exception:
        return {
            "status": "error",
            "message": f"nie można zrzutować {p.sym} na int",
            "notes": []
        }

    if N <= 2:
        return {
            "status": "skip",
            "message": "N ≤ 2 — brak sensownego widma liczb pierwszych",
            "notes": []
        }

    N_third = int(round(N ** (1/3)))
    if N_third < 3:
        N_third = 3

    primes = list(primerange(2, N_third + 1))

    if len(primes) < 2:
        return {
            "status": "ok",
            "prime_count": len(primes),
            "primes": primes,
            "gaps": [],
            "ratios": [],
            "spectrum_type": "too_few_primes",
            "notes": ["za mało liczb pierwszych w zakresie N^(1/3)"]
        }

    gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]
    ratios = [primes[i+1] / primes[i] for i in range(len(primes) - 1)]

    spectrum_type, diff_value, null_threshold = _classify_spectrum(gaps)

    notes = [
        f"N = {N}",
        f"zakres pierwszych: do N^(1/3) ≈ {N_third}",
        f"liczba pierwszych w zakresie: {len(primes)}",
    ]
    if diff_value is not None:
        thr_str = f"{null_threshold:.4f}" if null_threshold is not None else "brak (numpy niedostępne)"
        notes.append(f"diff={diff_value:.4f}, prog_modelu_zerowego_5pct={thr_str}")
    if spectrum_type == "log_spiral_1_over_f":
        notes.append(
            "diff ponizej 5. percentyla modelu zerowego (1000 losowych ciagow "
            "o tej samej dlugosci/zakresie krokow) dla TEGO KONKRETNEGO N. "
            "UWAGA: to NIE jest potwierdzony zwiazek z TIMDR Lambda-tau-rho — "
            "sprawdzone empirycznie na niezaleznych oknach wzdluz prawdziwych "
            "liczb pierwszych (do 10^6): realne liczby pierwsze trafiaja w te "
            "etykiete RZADZIEJ niz oczekiwane ~5% z modelu zerowego (0.3%-2.7% "
            "w zaleznosci od dlugosci okna), nie czesciej. Traktuj te etykiete "
            "jako wynik jednego waskiego testu statystycznego dla tego N, nie "
            "jako wlasnosc liczb pierwszych w ogole."
        )

    return {
        "status": "ok",
        "prime_count": len(primes),
        "primes": primes,
        "gaps": gaps,
        "ratios": ratios,
        "spectrum_type": spectrum_type,
        "diff_metric": diff_value,
        "null_threshold_5pct": null_threshold,
        "notes": notes,
    }
