"""Verdikte: jede Zahl im Text stammt aus der Rechnung (DEMO-PLAYBOOK §9). Die Verdikte sind reine Funktionen (Art, Text); hier wird jede Verzweigung einmal erreicht."""

import re

import swp_constants as C
import swp_evaluation as ev
import swp_savings as S
import swp_sweep as W


def _corner_analysis(corner, monkeypatch):
    monkeypatch.setattr(ev, "build_instance", lambda settings: corner)
    return ev.analyse(ev.Settings(6, 0, 1, 2, 90, 13))


def test_compare_verdict_when_the_sweep_is_dearer_by_hand(corner, monkeypatch):
    a = _corner_analysis(corner, monkeypatch)
    kind, text = ev.verdict_compare(a)
    assert kind == "warning" and "Sweep (bester Start) 91,54 (17,7 % über dem Optimum 77,79), Savings (λ = 1) 77,79 (0,0 %), Einfügen nach Split 77,79 (0,0 %)" in text and "Der Sweep ist 17,7 % teurer als Savings" in text
    assert "billigste" not in text


def test_compare_verdict_when_the_sweep_is_cheaper_and_when_it_is_the_cheapest():
    kind, text = ev.verdict_compare(ev.analyse(ev.Settings(8, 1, 1, 3, 90, 0)))
    assert kind == "success" and "Sweep (bester Start) 511,32 (0,0 %" in text and "Der Sweep ist 14,3 % billiger als Savings" in text and "Er ist hier das billigste der drei Verfahren" in text
    kind, text = ev.verdict_compare(ev.analyse(ev.Settings(8, 1, 0, 3, 90, 1)))
    assert kind == "success" and "Der Sweep ist 3,2 % billiger als Savings" in text and "billigste" not in text                    # Einfügen nach Split ist gleich billig


def test_compare_verdict_when_both_are_nearly_level():
    kind, text = ev.verdict_compare(ev.analyse(ev.Settings(12, 1, 0, 3, 98, 11)))
    assert kind == "warning" and "10,7 %" in text and "Der Sweep ist 0,7 % teurer als Savings" in text


def test_starts_verdict_by_hand(corner, monkeypatch):
    a = _corner_analysis(corner, monkeypatch)
    kind, text = ev.verdict_starts(a)
    assert kind == "info" and "Von 12 Starts" in text and "der feste Start 93,73 (20,5 % über dem Optimum 77,79)" in text and "der beste (Position 2, mit dem Uhrzeigersinn) 91,54 (17,7 %)" in text
    assert "der schlechteste 96,00 (23,4 %)" in text and "4 verschiedene Kosten" in text and "Kein Start braucht mehr als die Mindestroutenzahl 2 Routen" in text


def test_starts_verdict_with_the_optimum_and_with_extra_routes():
    kind, text = ev.verdict_starts(ev.analyse(ev.Settings(8, 1, 1, 3, 90, 0)))
    assert kind == "success" and "der feste Start 805,37 (57,5 %" in text and "der beste (Position 1, mit dem Uhrzeigersinn) 511,32 (0,0 %)" in text and "6 der 16 Starts brauchen mehr als die Mindestroutenzahl 3 Routen" in text


def test_losses_verdict_with_and_without_a_sweep_partition(corner, monkeypatch):
    kind, text = ev.verdict_losses(_corner_analysis(corner, monkeypatch))
    assert kind == "warning" and "Schnittoptimum) kostet 91,54 (17,7 % darüber)" in text and "Der feste Start mit „Füllen bis voll“ kostet 93,73 (20,5 %)" in text and "Schnitt-Verlust gegen das Schnittoptimum ist 2,4 %" in text
    assert "116,32 (49,5 %)" in text and "Das Optimum ist keine Sweep-Zerlegung" in text
    monkeypatch.undo()
    kind, text = ev.verdict_losses(ev.analyse(ev.Settings(8, 1, 1, 3, 90, 0)))
    assert kind == "success" and "Das Optimum besteht aus zusammenhängenden Stücken der Winkelfolge" in text and "Schnitt-Verlust gegen das Schnittoptimum ist 57,5 %" in text


def test_sweep_verdict_with_and_without_extra_routes():
    s = ev.Settings(8, 1, 1, 3, 90, 0)
    a = ev.analyse(s)
    kind, text = ev.verdict_sweep(a, 0, 1, True, ev.sweep_view(s, 0, 1, True))
    assert kind == "warning" and "Sweep ab Position 1 der Winkelfolge, gegen den Uhrzeigersinn, kürzeste Rundreise je Cluster: 4 Routen mit den Lasten 8, 5, 11, 7 (Kapazität 12)" in text
    assert "Länge 805,37, 57,5 % über dem Optimum 511,32" in text and "braucht 4 Routen; die Mindestroutenzahl ist 3" in text
    kind, text = ev.verdict_sweep(a, 0, -1, True, ev.sweep_view(s, 0, -1, True))
    assert kind == "success" and "mit dem Uhrzeigersinn" in text and "0,0 % über dem Optimum 511,32" in text and "Mindestroutenzahl" not in text
    s1 = ev.Settings(8, 1, 0, 3, 90, 1)
    a1 = ev.analyse(s1)
    kind, text = ev.verdict_sweep(a1, 0, 1, False, ev.sweep_view(s1, 0, 1, False))
    assert kind == "success" and "Winkelfolge je Cluster: 3 Routen mit den Lasten 13, 15, 15 (Kapazität 16)" in text


def test_sweep_view_table_and_loads_by_hand(corner, monkeypatch):
    monkeypatch.setattr(ev, "build_instance", lambda settings: corner)
    view = ev.sweep_view(ev.Settings(6, 0, 1, 2, 90, 13), 0, 1, True)
    assert view["order"] == (4, 5, 1, 2, 6, 3) and view["loads"] == [11, 8]
    assert [(r["customer"], round(r["angle"], 1), r["demand"], r["cluster"]) for r in view["table"]] == [(4, 14.0, 1, 1), (5, 26.6, 4, 1), (1, 43.0, 3, 1), (2, 47.1, 3, 1), (6, 50.9, 4, 2), (3, 85.6, 4, 2)]
    assert round(view["table"][1]["distance"], 2) == 2.24 and round(view["plan"].cost, 2) == 93.73


def test_band_verdicts_state_the_counts_of_the_stored_rows():
    stats = ev.band_stats(ev.band_rows(12, 90))
    kind, text = ev.verdict_bands(12, 90, 3, stats)
    vs = stats["vs"]["swb"]
    assert kind == "info" and "Bei n = 12, 3 Routen, Auslastung 90 % (80 Instanzen)" in text and "Abstand zum exakten Optimum" in text and f"{vs['cheaper']} / {vs['equal']} / {vs['more']} von 80" in text
    assert "Savings (λ = 1 + Rundreise) liegt im Median vor dem Sweep" in text and "Sweep, bester Start + Rundreise Median 2,3 %" in text
    kind, text = ev.verdict_bands(50, 90, 8, ev.band_stats(ev.band_rows(50, 90, 8)))
    assert kind == "warning" and "Savings (λ = 1 + Rundreise) liegt im Median vor dem Sweep" in text and "Abstand zur Referenz PyVRP (keine bewiesene Untergrenze)" in text and "8 Routen" in text
    kind, text = ev.verdict_bands(50, 90, 3, ev.band_stats(ev.band_rows(50, 90)))
    assert "liegt im Median vor Savings" in text and "23 / 0 / 9 von 32" in text
    assert ev.verdict_bands(12, 90, 3, {})[0] == "warning"


def test_band_verdict_level_case():
    base = {"count": 4, "gaps": {k: {"median": 1.0, "max": 2.0} for k in C.STRATEGY_KEYS}, "vs": {"swb": {"cheaper": 2, "equal": 0, "more": 2, "median_diff": 0.4, "count": 4}}}
    assert "im Median gleichauf (Unterschied +0,4 %" in ev.verdict_bands(12, 90, 3, base)[1]
    base["gaps"]["swb"]["median"] = 6.0
    assert ev.verdict_bands(25, 90, 3, base)[0] == "warning"


def test_fleet_optimum_and_depot_verdicts():
    stats = ev.band_stats(ev.band_rows(12, 98))
    kind, text = ev.verdict_fleet(stats)
    assert kind == "warning" and f"in {stats['over_m']} von 80 Instanzen" in text and "Das Optimum fährt in 14 Instanzen mehr als m Routen" in text
    kind, text = ev.verdict_fleet(ev.band_stats(ev.band_rows(25, 90)))
    assert kind == "info" and "in 0 von 32 Instanzen" in text and "Das Optimum fährt" not in text
    assert "in 16 von 80 Instanzen" in ev.verdict_optimum_sweep(stats)[1] and "kein exaktes Optimum" in ev.verdict_optimum_sweep(ev.band_stats(ev.band_rows(25, 90)))[1]
    kind, text = ev.verdict_depot(ev.band_stats(ev.band_rows(12, 90)))
    assert "Depot in der Mitte 0,1 %, in der Ecke 4,4 %" in text and "Für den Sweep ist die Ecke hier schlechter" in text
    fake = {"by_depot": {0: {"swb": 4.0, "sp1_r": 1.0}, 1: {"swb": 2.0, "sp1_r": 1.0}}}
    assert "nicht schlechter" in ev.verdict_depot(fake)[1] and ev.verdict_depot({})[0] == "warning" and ev.verdict_fleet({})[0] == "warning"


def test_every_preset_produces_all_verdicts():
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["n"], preset["family"], preset["depot"], preset["routes"], preset["fill"], preset["seed"])
        a = ev.analyse(s)
        view = ev.sweep_view(s, 0, 1, True)
        for kind, text in (ev.verdict_compare(a), ev.verdict_starts(a), ev.verdict_losses(a), ev.verdict_sweep(a, 0, 1, True, view)):
            assert kind in ("success", "info", "warning") and text and re.search(r"\bnan\b", text.lower()) is None
