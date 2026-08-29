"""
test_prime_spectrum_null_model.py — testy dla DRUGIEJ naprawy
prime_spectrum_filter.py (rekalibracja na model Cramera/Gallaghera).

Kontekst (patrz naglowek filtra dla pelnego opisu): pierwsza naprawa
(zachowana w git log) zastapila sztywny prog 0.25 modelem zerowym, ale
sama metryka ("ksztalt gaps vs log(x)") pozostala ad hoc. Test wypadl
negatywnie — realne pierwsze nie odrozznialy sie od losowych ciagow.
Uzytkownik zapytal: zla metryka, czy naprawde brak struktury? Sesja
kalibracyjna z prawdziwym modelem Cramera (znormalizowana luka
gap/log(p) ~ Exp(1) asymptotycznie) pokazala: struktura JEST widoczna
(srednia=1.0017 zgodna z teoria; statystycznie istotna korelacja
sasiednich luk r=-0.057, p≈4e-57) — negatywny wynik pierwszej naprawy
byl artefaktem zlej metryki/"plaszczyzny", nie braku struktury.

Te testy pilnuja: (1) filtr jawnie odmawia klasyfikacji, gdy ma za malo
luk (<30) zamiast zgadywac — to bezposrednia naprawa nadmiernej
pewnosci starej wersji; (2) pola nowej metodologii (mean_normalized_gap,
ks_statistic/pvalue, serial_correlation/pvalue) sa obecne i sensowne,
gdy jest wystarczajaco danych; (3) stare, niepoparte etykiety/twierdzenia
("log_spiral_1_over_f", zwiazek z TIMDR Lambda-tau-rho) NIE pojawiaja
sie juz nigdzie; (4) integracja z pipeline_v3.validate_all() nadal
dziala; (5) wlasne narzedzie statystyczne (_ks_two_sided_vs_exp1,
_serial_pearson_r) przechodzi te same kontrole negatywne, co w sesji
kalibracyjnej (i.i.d. Exp(1) -> KS nie odrzuca; ciag staly -> KS
wyraznie odrzuca).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

from core import parse
from filters import prime_spectrum_filter as psf
from pipeline_v3 import validate_all


def test_zbyt_malo_pierwszych_status_ok_pusty():
    """N tak male, ze N^(1/3) < 2 -> falls back do "too_few_primes"
    (ten najbardziej skrajny przypadek, sprzed obu napraw, bez zmian)."""
    r = psf.run(parse("50"))
    assert r["status"] == "ok"
    assert r["prime_count"] <= 2


def test_n_nie_calkowite_pomijane():
    r = psf.run(parse("x + 1"))
    assert r["status"] == "skip"


def test_n_male_pomijane():
    r = psf.run(parse("2"))
    assert r["status"] == "skip"


def test_male_n_daje_insufficient_data_nie_zgaduje():
    """Klucowa naprawa: N=999999 dawal kiedys PEWNA etykiete
    "log_spiral_1_over_f" na zaledwie 24 lukach. Nowa wersja: <30 luk ->
    filtr jawnie mowi "za malo danych", zamiast klasyfikowac."""
    r = psf.run(parse("999999"))
    assert r["prime_count"] < 31  # N^(1/3)~100 -> 25 pierwszych -> 24 luki
    assert r["spectrum_type"] == "insufficient_data_for_cramer_test"
    assert r["mean_normalized_gap"] is None
    assert r["ks_pvalue"] is None


def test_wystarczajaco_duze_n_daje_pelna_klasyfikacje():
    """N=2_100_000 -> N^(1/3) ~ 128 -> >=31 pierwszych -> >=30 luk ->
    filtr POWINIEN policzyc pelna statystyke Cramera/Gallaghera."""
    r = psf.run(parse("2100000"))
    assert r["prime_count"] - 1 >= 30
    assert r["spectrum_type"] in ("cramer_consistent", "cramer_finite_size_deviation")
    assert r["mean_normalized_gap"] is not None
    assert r["mean_normalized_gap"] > 0
    assert r["ks_statistic"] is not None
    assert 0.0 <= r["ks_statistic"] <= 1.0
    assert r["ks_pvalue"] is not None
    assert 0.0 <= r["ks_pvalue"] <= 1.0


def test_klasyfikacja_deterministyczna():
    r1 = psf.run(parse("2100000"))
    r2 = psf.run(parse("2100000"))
    assert r1["spectrum_type"] == r2["spectrum_type"]
    assert r1["mean_normalized_gap"] == r2["mean_normalized_gap"]
    assert r1["ks_pvalue"] == r2["ks_pvalue"]
    assert r1["serial_correlation"] == r2["serial_correlation"]


def test_brak_starej_etykiety_log_spiral():
    """Etykieta wymyslona na potrzeby pierwszej wersji filtra (i jej
    powiazanie z TIMDR Lambda-tau-rho) zniknela calkowicie — zastapiona
    etykietami ugruntowanymi w modelu Cramera/Gallaghera."""
    for n in [50, 5000, 999999, 2100000, 10**12]:
        r = psf.run(parse(str(n)))
        assert r.get("spectrum_type") != "log_spiral_1_over_f"
        all_notes = " ".join(r.get("notes", []))
        assert "log_spiral" not in all_notes
        assert "Λ–τ–ρ" not in all_notes


def test_zastrzezenie_o_timdr_obecne_gdy_korelacja_istotna():
    """Jesli filtr zglasza istotna statystycznie korelacje sasiednich luk
    (realna struktura wykraczajaca poza model Cramera), notatka MUSI
    jawnie zastrzec, ze to nie jest potwierdzony zwiazek z TIMDR."""
    r = psf.run(parse("10000000000"))  # N^(1/3)=10000 -> 1229 pierwszych, duzo luk
    all_notes = " ".join(r["notes"])
    if r.get("serial_correlation_pvalue") is not None and r["serial_correlation_pvalue"] < psf.SIGNIFICANCE_ALPHA:
        assert "NIE jest potwierdzony zwiazek z" in all_notes


def test_integracja_z_pipeline_validate_all():
    r = validate_all("2100000")
    assert "prime_spectrum" in r
    assert r["prime_spectrum"]["status"] == "ok"
    assert "mean_normalized_gap" in r["prime_spectrum"]
    assert "serial_correlation" in r["prime_spectrum"]


# --- Kalibracja wlasnego narzedzia statystycznego (te same kontrole
# negatywne, co w sesji kalibracyjnej z uzytkownikiem) ---

def test_ks_nie_odrzuca_prawdziwego_exp1():
    rng = np.random.default_rng(0)
    x = list(rng.exponential(1.0, size=2000))
    d, p = psf._ks_two_sided_vs_exp1(x)
    assert p > 0.05, f"i.i.d. Exp(1) nie powinno byc odrzucone, p={p}"


def test_ks_odrzuca_ciag_staly():
    x = [1.0] * 2000
    d, p = psf._ks_two_sided_vs_exp1(x)
    assert p < 0.01, f"ciag staly powinien byc wyraznie odrzucony, p={p}"


def test_korelacja_bliska_zeru_na_iid_exp1():
    rng = np.random.default_rng(0)
    x = list(rng.exponential(1.0, size=5000))
    r, p = psf._serial_pearson_r(x)
    assert abs(r) < 0.05, f"i.i.d. dane nie powinny miec silnej autokorelacji, r={r}"


def test_prawdziwe_pierwsze_do_10_6_replikuja_wynik_sesji_kalibracyjnej():
    """Powtorzenie dokladnie tego testu, ktory wykonano w sesji z
    uzytkownikiem (78498 pierwszych do 10^6) - regresja pilnujaca, ze
    liczby z tej sesji (srednia~1.0017, korelacja r~-0.057) sa stabilne."""
    from sympy import primerange
    primes = list(primerange(2, 10**6 + 1))
    assert len(primes) == 78498
    gaps = [primes[i + 1] - primes[i] for i in range(len(primes) - 1)]
    x = psf._normalized_gaps(primes, gaps)
    mean_x = sum(x) / len(x)
    assert 0.95 < mean_x < 1.05
    r, p = psf._serial_pearson_r(x)
    assert -0.1 < r < -0.02
    assert p < 1e-10
