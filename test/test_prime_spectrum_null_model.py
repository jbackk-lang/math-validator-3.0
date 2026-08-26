"""
test_prime_spectrum_null_model.py — testy dla naprawy prime_spectrum_filter.py.

Kontekst: oryginalny filtr etykietował wynik "log_spiral_1_over_f" (z
dopisanym twierdzeniem o zwiazku z TIMDR Lambda-tau-rho) przy sztywnym progu
0.25, bez modelu zerowego. Zweryfikowano w sesji (protokol uzytkownika):
zbudowano model zerowy z losowych ciagow, ustalono prog jako 5. percentyl
tego rozkladu, i sprawdzono realne liczby pierwsze wzgledem niego - realne
pierwsze NIE przekraczaja progu czesciej niz losowe ciagi (nawet rzadziej:
0.3%-2.7% w niezaleznych oknach wzgledem oczekiwanych ~5%). Naprawiono:
prog liczony z modelu zerowego, a twierdzenie o TIMDR usuniete z notatek.

Te testy pilnuja: (1) klasyfikacja jest deterministyczna (ustalony seed),
(2) diff_metric i null_threshold_5pct sa zawsze zwracane gdy jest >=3 gaps,
(3) stare, niepoparte twierdzenie o TIMDR NIE pojawia sie juz w notatkach,
(4) integracja z pipeline_v3.validate_all() nadal dziala.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import parse
from filters import prime_spectrum_filter as psf
from pipeline_v3 import validate_all


def test_zbyt_malo_pierwszych():
    r = psf.run(parse("50"))
    assert r["spectrum_type"] == "too_few_primes"
    assert r["diff_metric"] is None
    assert r["null_threshold_5pct"] is None


def test_n_nie_calkowite_pomijane():
    r = psf.run(parse("x + 1"))
    assert r["status"] == "skip"


def test_n_male_pomijane():
    r = psf.run(parse("2"))
    assert r["status"] == "skip"


def test_diff_i_prog_obecne_gdy_wystarczajaco_gaps():
    r = psf.run(parse("5000"))
    assert r["diff_metric"] is not None
    assert r["null_threshold_5pct"] is not None
    # diff i prog musza byc liczbami dodatnimi (to srednia |roznica| znormalizowanych wartosci)
    assert r["diff_metric"] >= 0
    assert r["null_threshold_5pct"] >= 0


def test_klasyfikacja_deterministyczna():
    """Ten sam N -> ten sam wynik za kazdym razem (seed ustalony domyslnie)."""
    r1 = psf.run(parse("12345"))
    r2 = psf.run(parse("12345"))
    assert r1["spectrum_type"] == r2["spectrum_type"]
    assert r1["diff_metric"] == r2["diff_metric"]
    assert r1["null_threshold_5pct"] == r2["null_threshold_5pct"]


def test_prog_pochodzi_z_modelu_zerowego_nie_ze_stalej_0_25():
    """Zweryfikowane wprost w sesji: dla N=999999 stary sztywny prog 0.25 dawal
    'irregular' (diff=0.272 > 0.25), ale prog z modelu zerowego dla tej dlugosci
    gaps (25) wychodzi wyzej (~0.295), wiec NOWA klasyfikacja to log_spiral_1_over_f
    - inny wynik niz dawalby stary, ungruntowany prog. To potwierdza, ze prog
    faktycznie pochodzi z modelu zerowego, nie jest to sama stara stala pod inna nazwa."""
    r = psf.run(parse("999999"))
    assert r["null_threshold_5pct"] is not None
    assert abs(r["null_threshold_5pct"] - 0.25) > 0.01, (
        "prog wyszedl podejrzanie blisko starej stalej 0.25 - sprawdz czy model "
        "zerowy faktycznie jest uzywany"
    )
    assert r["spectrum_type"] == "log_spiral_1_over_f"


def test_brak_falszywego_twierdzenia_o_timdr_w_notatkach():
    """Stare zdanie 'widmo zgodne z logarytmiczna spirala / 1/f (Lambda-tau-rho/TIMDR)'
    twierdzilo o zwiazku z TIMDR bez zadnego wsparcia statystycznego - usuniete
    w calosci (ten dokladny string nie moze sie juz pojawic). Jesli etykieta
    log_spiral_1_over_f sie pojawia, notatka musi teraz jawnie zastrzegac, ze
    to NIE jest potwierdzony zwiazek z TIMDR."""
    old_claim = "widmo zgodne z logarytmiczną spiralą / 1/f (Λ–τ–ρ/TIMDR)"
    for n in [5000, 12345, 999999]:
        r = psf.run(parse(str(n)))
        all_notes = " ".join(r["notes"])
        assert old_claim not in all_notes, f"N={n}: stare, niepoparte twierdzenie o TIMDR nadal obecne"
        if r["spectrum_type"] == "log_spiral_1_over_f":
            assert "NIE jest potwierdzony" in all_notes, (
                f"N={n}: etykieta log_spiral_1_over_f bez jawnego zastrzezenia o braku "
                f"potwierdzenia zwiazku z TIMDR: {r['notes']}"
            )


def test_integracja_z_pipeline_validate_all():
    r = validate_all("999999")
    assert "prime_spectrum" in r
    assert r["prime_spectrum"]["status"] == "ok"
    assert "diff_metric" in r["prime_spectrum"]
    assert "null_threshold_5pct" in r["prime_spectrum"]
