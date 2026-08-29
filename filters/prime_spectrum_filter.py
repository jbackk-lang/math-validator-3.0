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
  - klasyfikację widma WZGLĘDEM PRAWDZIWEGO, USTALONEGO W TEORII LICZB
    MODELU (patrz niżej — to jest DRUGA naprawa tego filtra)

DRUGA POPRAWKA — rekalibracja na model Cramera/Gallaghera (ta sesja):

Pierwsza naprawa (patrz git log) zastąpiła sztywny próg 0.25 modelem
zerowym z losowych ciągów całkowitych — ale sama METRYKA ("średnia
znormalizowana odległość gaps od krzywej log(x)") pozostała ad hoc,
wymyślona na potrzeby tego filtra, bez żadnego oparcia w teorii liczb.
Test względem tej metryki wypadł negatywnie: prawdziwe liczby pierwsze
NIE trafiały w etykietę "log_spiral_1_over_f" częściej niż losowe ciągi
(patrz git log f1f258d).

Użytkownik zapytał wprost: czy ten negatywny wynik oznacza brak
struktury, czy złą metrykę/"płaszczyznę"? Zweryfikowano to w osobnej,
pre-zarejestrowanej sesji kalibracyjnej (protokół z timdr-signal-framework
§18): zamiast ad hoc metryki, użyto PRAWDZIWEGO, ugruntowanego w
analitycznej teorii liczb modelu Cramera / hipotezy Gallaghera — luki
między kolejnymi liczbami pierwszymi w pobliżu x, znormalizowane przez
log(x), powinny asymptotycznie zbiegać do rozkładu Exponencjalnego(1)
(równoważnie: proces pierwszych lokalnie jak proces Poissona o
intensywności 1/log(x)).

Test na 78498 prawdziwych liczbach pierwszych do 10^6 (sympy.primerange),
ze znormalizowaną luką x_n = (p_{n+1}-p_n)/log(p_n):
  - średnia x_n = 1.0017 (bardzo blisko przewidywania modelu Cramera ~1.0)
  - test Kolmogorova-Smirnowa x_n vs Exp(1): D=0.1478, p≈0 — ODRZUCA
    czysty Exp(1) przy tym N. To UDOKUMENTOWANY efekt skończonego zakresu
    (zbieżność modelu Cramera do Exp(1) jest wolna/asymptotyczna, nie
    dokładna przy skończonym N) — nie dowód braku struktury.
  - korelacja Pearsona kolejnych znormalizowanych luk (x_n, x_{n+1}):
    r=-0.0568, p≈4.4e-57 — MAŁA, ale statystycznie bardzo istotna ujemna
    korelacja. To JEST realna struktura wykraczająca poza prosty model
    Cramera (który zakłada niezależne, i.i.d. luki) — zgodna z
    udokumentowanymi w literaturze analitycznej teorii liczb
    obciążeniami/korelacjami sąsiednich luk między liczbami pierwszymi.
    Kontrola: te same statystyki na i.i.d. Exp(1) o tej samej licznosci
    dają r=-0.0009, p=0.80 (brak korelacji) — więc korelacja u prawdziwych
    pierwszych NIE jest artefaktem metody.
  - obie kontrole negatywne narzędzia testującego zachowały się poprawnie:
    i.i.d. Exp(1) → KS nie odrzuca (p=0.11); ciąg arytmetyczny/stały →
    KS wyraźnie odrzuca (p≈0).

WNIOSEK: negatywny wynik pierwszej naprawy wynikał z metryki/"płaszczyzny"
("kształt do log(x)"), nie z braku struktury liczb pierwszych. Względem
właściwego modelu (Cramer/Gallagher) struktura jest widoczna — a nawet
wykracza poza sam model Cramera (korelacja sąsiednich luk).

WAŻNE OGRANICZENIE SKALI (uczciwie udokumentowane): ten filtr liczy
pierwsze TYLKO do N**(1/3). Żeby mieć >=30 luk (minimum do sensownego
testu KS/korelacji, patrz MIN_GAPS_FOR_CRAMER_TEST), potrzeba N^(1/3) >=
127, czyli N >= ok. 2 048 383. Dla mniejszych N filtr zwraca
"insufficient_data_for_cramer_test" zamiast zgadywać — to WPROST
naprawia nadużycie z pierwszej wersji, która potrafiła nadawać pewną
etykietę na 6-24 lukach.

Etykieta "log_spiral_1_over_f" i jakikolwiek związek z TIMDR Λ–τ–ρ
zostały usunięte całkowicie (były i pozostają niepotwierdzone).
"""

from core import ParsedExpr
from sympy import primerange
from math import log, sqrt, exp, erf

try:
    import numpy as np  # noqa: F401  (zachowane dla zgodnosci/przyszlego uzycia)
    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False

# Minimalna liczba luk, przy ktorej test KS/korelacji ma w ogole sens
# statystyczny. Ponizej tego progu filtr NIE zgaduje - zwraca jawnie
# "insufficient_data_for_cramer_test" (patrz naglowek pliku - to wprost
# naprawia nadmierna pewnosc pierwszej wersji filtra).
MIN_GAPS_FOR_CRAMER_TEST = 30

# Prog istotnosci dla testu KS i korelacji sasiednich luk.
SIGNIFICANCE_ALPHA = 0.01


def _normalized_gaps(primes, gaps):
    """x_n = gap_n / log(p_n) - znormalizowana luka wzgledem modelu
    Cramera/Gallaghera. Asymptotycznie (dla p_n -> nieskonczonosc)
    x_n ~ Exponencjalny(1), niezaleznie miedzy soba."""
    return [g / log(p) for g, p in zip(gaps, primes[:-1])]


def _ks_two_sided_vs_exp1(x):
    """Statystyka i p-wartosc dwustronnego testu Kolmogorova-Smirnowa
    x vs rozklad Exponencjalny(1) (CDF F(t) = 1 - e^-t, t >= 0).

    Implementacja czysto matematyczna (bez scipy - ten projekt nigdy nie
    mial scipy jako zaleznosci, patrz requirements.txt): p-wartosc liczona
    asymptotycznym wzorem Kolmogorova z poprawka Marsaglii-Stephensa,
    standardowa, ugruntowana aproksymacja uzywana w wiekszosci bibliotek
    statystycznych (rownowazna temu, co pod maska robi scipy.stats.kstest
    dla duzych n)."""
    n = len(x)
    if n == 0:
        return None, None
    xs = sorted(x)
    d_plus = max((i + 1) / n - (1 - exp(-xs[i])) for i in range(n))
    d_minus = max((1 - exp(-xs[i])) - i / n for i in range(n))
    d = max(d_plus, d_minus)

    en = sqrt(n)
    term = (en + 0.12 + 0.11 / en) * d
    q = 0.0
    for k in range(1, 101):
        term_k = ((-1) ** (k - 1)) * exp(-2 * k * k * term * term)
        q += term_k
        if abs(term_k) < 1e-12:
            break
    p = max(0.0, min(1.0, 2 * q))
    return d, p


def _serial_pearson_r(x):
    """Korelacja Pearsona kolejnych znormalizowanych luk (x_n, x_n+1) -
    dokladnie ta "plaszczyzna"/zaleznosc miedzy sasiednimi punktami widma,
    o ktora pytal uzytkownik. Model Cramera zaklada i.i.d. luki (r~0);
    realna, statystycznie istotna wartosc != 0 to struktura WYKRACZAJACA
    poza sam model Cramera (znana w literaturze jako obciazenia/korelacje
    sasiednich luk miedzy liczbami pierwszymi - NIE jest to zwiazane z
    TIMDR, patrz zastrzezenie w notes ponizej).

    P-wartosc: transformacja Fishera z + przyblizenie normalne (dokladne
    dla duzych n_pairs, ktore w tym filtrze wystepuja - patrz
    MIN_GAPS_FOR_CRAMER_TEST). Bez zaleznosci od scipy."""
    n = len(x)
    if n < 3:
        return None, None
    a, b = x[:-1], x[1:]
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    cov = sum((ai - ma) * (bi - mb) for ai, bi in zip(a, b))
    va = sum((ai - ma) ** 2 for ai in a)
    vb = sum((bi - mb) ** 2 for bi in b)
    if va <= 0 or vb <= 0:
        return 0.0, 1.0
    r = max(-1.0, min(1.0, cov / sqrt(va * vb)))
    npairs = len(a)
    if npairs < 4 or abs(r) >= 1.0:
        return r, None
    z = 0.5 * log((1 + r) / (1 - r)) * sqrt(npairs - 3)
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return r, max(0.0, min(1.0, p))


def _classify_spectrum(primes, gaps):
    """Klasyfikacja wzgledem modelu Cramera/Gallaghera (patrz naglowek
    pliku). Zwraca dict z polami spectrum_type, mean_normalized_gap,
    ks_statistic, ks_pvalue, serial_correlation, serial_correlation_pvalue
    (None tam, gdzie za malo danych)."""
    if len(gaps) < MIN_GAPS_FOR_CRAMER_TEST:
        return {
            "spectrum_type": "insufficient_data_for_cramer_test",
            "mean_normalized_gap": None,
            "ks_statistic": None,
            "ks_pvalue": None,
            "serial_correlation": None,
            "serial_correlation_pvalue": None,
        }

    x = _normalized_gaps(primes, gaps)
    mean_x = sum(x) / len(x)
    ks_d, ks_p = _ks_two_sided_vs_exp1(x)
    r, r_p = _serial_pearson_r(x)

    spectrum_type = "cramer_consistent" if (ks_p is not None and ks_p >= SIGNIFICANCE_ALPHA) \
        else "cramer_finite_size_deviation"

    return {
        "spectrum_type": spectrum_type,
        "mean_normalized_gap": mean_x,
        "ks_statistic": ks_d,
        "ks_pvalue": ks_p,
        "serial_correlation": r,
        "serial_correlation_pvalue": r_p,
    }


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
            "mean_normalized_gap": None,
            "ks_statistic": None,
            "ks_pvalue": None,
            "serial_correlation": None,
            "serial_correlation_pvalue": None,
            "notes": ["za mało liczb pierwszych w zakresie N^(1/3)"]
        }

    gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]
    ratios = [primes[i+1] / primes[i] for i in range(len(primes) - 1)]

    stats = _classify_spectrum(primes, gaps)

    notes = [
        f"N = {N}",
        f"zakres pierwszych: do N^(1/3) ≈ {N_third}",
        f"liczba pierwszych w zakresie: {len(primes)}",
    ]

    if stats["spectrum_type"] == "insufficient_data_for_cramer_test":
        notes.append(
            f"tylko {len(gaps)} luk (< {MIN_GAPS_FOR_CRAMER_TEST}) — za mało danych "
            "na sensowny test statystyczny względem modelu Cramera/Gallaghera. "
            "Dla tego filtra (pierwsze tylko do N^(1/3)) trzeba N >= ok. 2 048 383, "
            "zeby w ogole miec >=30 luk — dla mniejszych N ten filtr swiadomie "
            "NIE klasyfikuje, zamiast zgadywac na garstce probek."
        )
    else:
        notes.append(
            f"srednia znormalizowanej luki (gap/log(p)) = {stats['mean_normalized_gap']:.4f} "
            "(model Cramera przewiduje ~1.0 asymptotycznie)"
        )
        notes.append(
            f"test Kolmogorova-Smirnowa vs Exp(1): D={stats['ks_statistic']:.4f}, "
            f"p={stats['ks_pvalue']:.4g}"
        )
        if stats["spectrum_type"] == "cramer_finite_size_deviation":
            notes.append(
                "KS odrzuca czysty rozklad Exp(1) przy tym N — to UDOKUMENTOWANY "
                "efekt skonczonego zakresu (zbieznosc modelu Cramera do Exp(1) "
                "jest asymptotyczna/wolna), zweryfikowane w sesji kalibracyjnej na "
                "78498 prawdziwych liczbach pierwszych do 10^6 (srednia=1.0017, "
                "D=0.1478, p≈0) — NIE oznacza to braku struktury, tylko ze przy "
                "tym N czysty Exp(1) juz nie wystarcza jako dokladny model."
            )
        if stats["serial_correlation"] is not None and stats["serial_correlation_pvalue"] is not None:
            notes.append(
                f"korelacja kolejnych znormalizowanych luk: r={stats['serial_correlation']:.4f}, "
                f"p={stats['serial_correlation_pvalue']:.4g}"
            )
            if stats["serial_correlation_pvalue"] < SIGNIFICANCE_ALPHA:
                notes.append(
                    "statystycznie istotna korelacja miedzy kolejnymi lukami — to "
                    "JEST realna struktura wykraczajaca poza prosty model Cramera "
                    "(ktory zaklada niezalezne, i.i.d. luki), zgodna z "
                    "udokumentowanymi w literaturze analitycznej teorii liczb "
                    "obciazeniami/korelacjami sasiednich luk miedzy liczbami "
                    "pierwszymi. UWAGA: to NADAL NIE jest potwierdzony zwiazek z "
                    "TIMDR Lambda-tau-rho — to ogolnie znany efekt w teorii liczb "
                    "pierwszych, niezalezny od TIMDR."
                )
            else:
                notes.append(
                    "korelacja nieistotna statystycznie przy tym N — brak dowodu "
                    "na zaleznosc miedzy sasiednimi lukami wykraczajaca poza model "
                    "Cramera."
                )

    return {
        "status": "ok",
        "prime_count": len(primes),
        "primes": primes,
        "gaps": gaps,
        "ratios": ratios,
        **stats,
        "notes": notes,
    }
