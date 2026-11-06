"""Die fünf Experimente der App per AppTest: Sweep Schritt für Schritt (Start, Richtung, Reihenfolge im Cluster), Starts, Verluste, Vergleich und Bänder (inklusive kurzer Routen); dazu das PDF."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import swp_constants as C
import swp_evaluation as ev
from swp_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SHORT = f"Kurze Routen ({C.SHORT_N} Kunden, {C.SHORT_ROUTES} Zielrouten)"
SETTING_KEYS = {"n": "n_slider", "family": "family_select", "depot": "depot_select", "routes": "routes_slider", "fill": "fill_slider", "seed": "seed_input"}


def _app(preset=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if preset:
        at.session_state["permalink_loaded"] = True
        for key, state_key in SETTING_KEYS.items():
            at.session_state[state_key] = C.PRESETS[preset][key]
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join([x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning])


def test_start_direction_and_routing_controls_change_the_sweep():
    at = _app("Der Start entscheidet (n = 8, Depot in der Ecke)")
    assert "Sweep ab Position 1 der Winkelfolge, gegen den Uhrzeigersinn, kürzeste Rundreise je Cluster: 4 Routen" in _texts(at) and "843,89" in _texts(at)
    at.radio(key="dir_radio").set_value("mit dem Uhrzeigersinn").run()
    assert not at.exception and "mit dem Uhrzeigersinn, kürzeste Rundreise je Cluster: 3 Routen" in _texts(at) and "3,5 % über dem Optimum 703,27" in _texts(at)
    at.radio(key="routing_radio").set_value("Winkelfolge").run()
    assert not at.exception and "Winkelfolge je Cluster" in _texts(at)
    for k in (1, 4, 8):
        at.slider(key="start_slider_8").set_value(k).run()
        assert not at.exception and f"Sweep ab Position {k} der Winkelfolge" in _texts(at)


def test_the_start_slider_follows_the_number_of_customers():
    at = _app()
    assert at.slider(key="start_slider_8").max == 8
    at.slider(key="n_slider").set_value(12).run()
    assert not at.exception and at.slider(key="start_slider_12").max == 12


def test_hand_preset_numbers_in_the_verdicts():
    text = _texts(_app("Ein Kunde nahe am Depot sprengt den Keil (n = 6)"))
    assert "der feste Start 93,73 (20,5 % über dem Optimum 77,79)" in text and "kostet 91,54 (17,7 % darüber)" in text and "Das Optimum ist keine Sweep-Zerlegung" in text


def test_changing_the_compared_plans_does_not_break_the_page():
    at = _app()
    for left in C.STRATEGY_KEYS:
        for right in ("swb", "sp1_r", "es_r"):
            at.selectbox(key="compare_left").set_value(left)
            at.selectbox(key="compare_right").set_value(right)
            at.run()
            assert not at.exception, (left, right)


def test_strategy_table_names_every_method():
    at = _app()
    table = [m.value for m in at.markdown if m.value.startswith("| Verfahren | Kosten | über Optimum | Routen | gegen Savings")][0]
    assert all(C.STRATEGY_NAMES[k] in table for k in C.STRATEGY_KEYS)


def test_band_selection_for_every_size_and_fill():
    at = _app()
    for n in C.BAND_SIZES:
        at.radio(key="band_n").set_value(n).run()
        assert not at.exception, n
        for fill in C.BAND_FILLS[n]:
            at.radio(key=f"band_fill_{n}_{C.BAND_ROUTES}").set_value(fill).run()
            assert not at.exception, (n, fill)
            assert f"Bei n = {n}, 3 Routen, Auslastung {fill} %" in _texts(at)


def test_short_routes_option_shows_the_eight_route_bands():
    at = _app()
    at.radio(key="band_kind").set_value(SHORT).run()
    assert not at.exception and f"Bei n = {C.SHORT_N}, {C.SHORT_ROUTES} Routen, Auslastung 90 %" in _texts(at)
    at.radio(key=f"band_fill_{C.SHORT_N}_{C.SHORT_ROUTES}").set_value(98).run()
    assert not at.exception and "Auslastung 98 %" in _texts(at)


def test_pdf_download_button_exists_and_the_pdf_is_built_for_every_preset():
    assert len(_app().get("download_button")) == 1
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["n"], preset["family"], preset["depot"], preset["routes"], preset["fill"], preset["seed"])
        data = build_pdf(s, ev.analyse(s))
        assert data[:5] == b"%PDF-" and len(data) > 1500
