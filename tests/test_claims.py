"""Jede Zahl der README („Befunde“) und der Preset-Hilfen, nachgerechnet mit denselben Funktionen wie die App (DEMO-PLAYBOOK §4).

Die Bänder kommen aus swp_bands.json (tests/test_bands.py rechnet Stichproben davon frisch nach); Werte werden auf eine Stelle verglichen. Die Zahlen wurden in der Planung
(vormessung/messreihe_tb25 bis tb28) mit eigenen Skripten unabhängig bestimmt und stimmen überein. Zeiten werden nicht festgeschrieben."""

import dataclasses
from pathlib import Path

import pytest

import swp_algorithm as A
import swp_constants as C
import swp_evaluation as ev
import swp_savings as S
import swp_sweep as W

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def r1(x):
    return round(x, 1)


def _stats(n, fill, routes=3):
    return ev.band_stats(ev.band_rows(n, fill, routes))


# Zelle (n, Auslastung, Zielrouten) -> je Verfahren (Median, Mittel, Maximum, getroffen); Sweep (bester Start) gegen Savings + Rundreise (billiger, gleich, teurer, Median des Unterschieds);
# Sweep mit festem Start braucht mehr als m Routen; Anteil der Starts mit mehr als m Routen in Prozent; Optimum ist Sweep-Zerlegung; Optimum fährt mehr als m Routen;
# Median nach Depot (Mitte, Ecke) für Sweep bester Start und Savings + Rundreise; Verluste (Cluster, Schnitt, Routing)
CELLS = {
    (10, 90, 3): dict(gaps={'sw0_order': (11.3, 15.6, 53.4, 3), 'sw0': (6.1, 10.8, 49.2, 11), 'swb_order': (4.4, 7.8, 39.0, 7), 'swb': (1.3, 4.3, 21.9, 28), 'splitb': (4.4, 7.8, 39.0, 7), 'cut': (1.3, 4.2, 21.4, 28), 'sp1': (0.2, 1.8, 15.0, 35), 'sp1_r': (0.0, 1.6, 15.0, 42), 'lam9_r': (0.0, 0.9, 11.1, 48), 'es': (0.0, 1.1, 10.0, 40), 'es_r': (0.0, 0.9, 10.0, 50)}, vs=(20, 17, 43, 0.4), fleet=(22, 26, 28, 3),
          depot=((0.0, 0.1), (3.7, 0.0)), losses=(1.3, 0.9, 1.7)),
    (12, 60, 3): dict(gaps={'sw0_order': (16.6, 20.3, 78.5, 0), 'sw0': (3.6, 6.2, 54.9, 16), 'swb_order': (10.1, 12.9, 57.0, 3), 'swb': (0.0, 1.4, 14.2, 39), 'splitb': (10.1, 12.9, 57.0, 3), 'cut': (0.0, 1.4, 14.2, 39), 'sp1': (0.7, 2.0, 12.0, 23), 'sp1_r': (0.0, 1.4, 12.0, 42), 'lam9_r': (0.0, 0.8, 6.7, 50), 'es': (0.7, 1.8, 15.8, 19), 'es_r': (0.0, 1.1, 13.5, 45)}, vs=(26, 30, 24, 0.0), fleet=(1, 2, 39, 0),
          depot=((0.0, 0.0), (1.1, 0.4)), losses=(0.0, 1.0, 10.6)),
    (12, 75, 3): dict(gaps={'sw0_order': (16.9, 21.1, 69.2, 0), 'sw0': (11.7, 12.6, 31.9, 0), 'swb_order': (10.1, 11.7, 40.5, 2), 'swb': (3.7, 4.7, 17.0, 11), 'splitb': (9.4, 10.8, 40.5, 2), 'cut': (2.3, 3.8, 17.0, 26), 'sp1': (1.0, 2.3, 15.6, 29), 'sp1_r': (0.0, 2.0, 15.6, 43), 'lam9_r': (0.0, 1.1, 12.1, 50), 'es': (0.5, 1.8, 11.0, 30), 'es_r': (0.0, 1.5, 10.7, 46)}, vs=(16, 7, 57, 2.1), fleet=(0, 0, 26, 0),
          depot=((2.8, 0.0), (5.0, 0.3)), losses=(2.3, 6.3, 5.4)),
    (12, 90, 3): dict(gaps={'sw0_order': (16.4, 21.2, 91.4, 0), 'sw0': (7.9, 12.5, 55.7, 6), 'swb_order': (9.0, 10.6, 39.6, 4), 'swb': (2.3, 4.2, 25.9, 25), 'splitb': (9.0, 10.4, 39.6, 4), 'cut': (2.3, 4.2, 25.9, 25), 'sp1': (0.8, 1.7, 9.9, 31), 'sp1_r': (0.3, 1.5, 9.9, 38), 'lam9_r': (0.0, 0.8, 7.9, 47), 'es': (0.6, 1.8, 15.3, 32), 'es_r': (0.0, 1.5, 15.3, 43)}, vs=(25, 8, 47, 1.7), fleet=(20, 22, 25, 0),
          depot=((0.1, 0.2), (4.4, 0.3)), losses=(2.3, 3.4, 6.0)),
    (12, 98, 3): dict(gaps={'sw0_order': (24.7, 25.6, 82.5, 1), 'sw0': (18.4, 18.8, 63.5, 3), 'swb_order': (13.8, 14.1, 38.3, 4), 'swb': (7.2, 8.7, 28.6, 14), 'splitb': (12.7, 13.5, 38.3, 4), 'cut': (6.1, 8.1, 28.3, 16), 'sp1': (2.0, 4.8, 26.6, 23), 'sp1_r': (1.9, 4.7, 26.5, 27), 'lam9_r': (0.2, 1.9, 15.9, 39), 'es': (1.0, 2.7, 15.7, 22), 'es_r': (0.8, 2.5, 15.7, 29)}, vs=(20, 7, 53, 2.4), fleet=(67, 78, 16, 14),
          depot=((5.2, 0.9), (10.4, 2.3)), losses=(6.1, 6.8, 3.8)),
    (25, 90, 3): dict(gaps={'sw0_order': (41.1, 40.4, 84.3, 0), 'sw0': (6.9, 7.4, 25.1, 1), 'swb_order': (28.2, 32.5, 79.0, 0), 'swb': (1.3, 3.1, 22.2, 3), 'splitb': (28.2, 32.2, 79.0, 0), 'cut': (1.3, 3.1, 22.2, 5), 'sp1': (2.4, 3.1, 10.7, 0), 'sp1_r': (1.3, 2.3, 10.6, 3), 'lam9_r': (0.5, 1.2, 6.6, 5), 'es': (3.3, 5.1, 18.8, 0), 'es_r': (2.6, 3.6, 18.4, 4)}, vs=(13, 6, 13, 0.0), fleet=(0, 0, None, None),
          depot=((0.3, 1.3), (2.6, 1.2)), losses=(1.3, 2.1, 26.9)),
    (50, 90, 3): dict(gaps={'sw0_order': (83.8, 92.2, 176.3, 0), 'sw0': (6.6, 9.5, 34.4, 0), 'swb_order': (68.3, 78.9, 165.9, 0), 'swb': (2.9, 4.1, 21.6, 2), 'splitb': (65.8, 77.3, 160.4, 0), 'sp1': (7.7, 7.7, 19.7, 0), 'sp1_r': (5.4, 5.5, 15.5, 0), 'lam9_r': (2.1, 3.0, 12.8, 1), 'es': (8.3, 9.1, 17.4, 0), 'es_r': (5.7, 5.7, 13.2, 1)}, vs=(23, 0, 9, -1.4), fleet=(0, 0, None, None),
          depot=((1.4, 5.9), (3.7, 4.3)), losses=None),
    (100, 90, 3): dict(gaps={'sw0_order': (145.5, 164.0, 282.9, 0), 'sw0': (7.0, 8.3, 24.3, 0), 'swb_order': (132.3, 155.0, 280.9, 0), 'swb': (4.5, 4.7, 14.6, 0), 'splitb': (129.4, 150.4, 278.4, 0), 'sp1': (9.2, 9.7, 18.2, 0), 'sp1_r': (7.1, 6.8, 14.6, 0), 'lam9_r': (4.0, 4.2, 11.2, 0), 'es': (11.7, 13.2, 24.9, 0)}, vs=(23, 0, 9, -2.7), fleet=(0, 0, None, None),
          depot=((3.7, 7.2), (4.8, 6.8)), losses=None),
    (50, 90, 8): dict(gaps={'sw0_order': (47.0, 49.0, 86.9, 0), 'sw0': (14.8, 14.8, 27.5, 0), 'swb_order': (34.6, 38.4, 79.3, 0), 'swb': (9.9, 10.6, 26.1, 0), 'splitb': (32.7, 36.7, 76.2, 0), 'sp1': (3.3, 3.6, 8.4, 0), 'sp1_r': (2.9, 3.2, 7.2, 0), 'lam9_r': (2.2, 2.4, 5.7, 0), 'es': (5.6, 6.8, 17.1, 0), 'es_r': (4.6, 5.4, 13.8, 0)}, vs=(2, 0, 30, 7.4), fleet=(1, 2, None, None),
          depot=((7.8, 3.8), (12.6, 2.4)), losses=None),
    (50, 98, 8): dict(gaps={'sw0_order': (46.7, 50.9, 106.8, 0), 'sw0': (18.5, 18.5, 30.9, 0), 'swb_order': (33.7, 38.4, 69.1, 0), 'swb': (14.1, 14.1, 28.9, 0), 'splitb': (33.0, 36.7, 66.9, 0), 'sp1': (3.4, 4.2, 11.7, 0), 'sp1_r': (3.3, 3.9, 11.7, 0), 'lam9_r': (1.9, 2.5, 6.8, 0), 'es': (6.6, 7.3, 15.9, 0), 'es_r': (5.4, 6.2, 13.3, 0)}, vs=(1, 0, 31, 9.3), fleet=(30, 96, None, None),
          depot=((9.8, 4.7), (17.0, 2.4)), losses=None),
}


@pytest.mark.parametrize("cell", list(CELLS))
def test_every_cell(cell):
    e = CELLS[cell]
    s = _stats(*cell)
    assert s["count"] == (80 if cell[0] in C.EXACT_SIZES else 32)
    for key, value in e["gaps"].items():
        g = s["gaps"][key]
        assert (r1(g["median"]), r1(g["mean"]), r1(g["max"]), g["hit"]) == value, key
    assert set(e["gaps"]) == set(s["gaps"])
    v = s["vs"]["swb"]
    assert (v["cheaper"], v["equal"], v["more"], r1(v["median_diff"])) == e["vs"]
    assert (s["over_m"], round(100 * s["over_m_share"]), s.get("opt_is_sweep"), s.get("opt_over_m")) == e["fleet"]
    assert tuple((r1(s["by_depot"][d]["swb"]), r1(s["by_depot"][d]["sp1_r"])) for d in (0, 1)) == e["depot"]
    if "cluster_loss" in s:
        assert (r1(s["cluster_loss"]["median"]), r1(s["cut_loss"]), r1(s["routing_loss"])) == e["losses"]
    else:
        assert e["losses"] is None


def test_the_readme_names_the_numbers_of_the_main_table():
    for cell, e in CELLS.items():
        for key in ("sw0", "swb", "sp1_r", "lam9_r", "es_r"):
            if key in e["gaps"]:
                median, mean, mx, _ = e["gaps"][key]
                assert f"{median:.1f} / {mean:.1f} / {mx:.1f}".replace(".", ",") in README, (cell, key)
        assert " / ".join(map(str, e["vs"][:3])) in README, cell


def test_the_readme_names_the_numbers_of_the_loss_depot_and_fleet_rows():
    assert [r1(CELLS[(12, f, 3)]["losses"][0]) for f in (60, 75, 90, 98)] == [0.0, 2.3, 2.3, 6.1] and CELLS[(10, 90, 3)]["losses"][0] == 1.3 and CELLS[(25, 90, 3)]["losses"][0] == 1.3
    assert [CELLS[(12, f, 3)]["losses"][1:] for f in (60, 75, 90, 98)] == [(1.0, 10.6), (6.3, 5.4), (3.4, 6.0), (6.8, 3.8)] and CELLS[(25, 90, 3)]["losses"][2] == 26.9
    assert [CELLS[(12, f, 3)]["fleet"][0] for f in (60, 75, 90, 98)] == [1, 0, 20, 67] and [CELLS[(12, f, 3)]["fleet"][1] for f in (60, 75, 90, 98)] == [2, 0, 22, 78]
    assert [CELLS[(12, f, 3)]["fleet"][2] for f in (60, 75, 90, 98)] == [39, 26, 25, 16] and CELLS[(10, 90, 3)]["fleet"][2] == 28 and CELLS[(12, 98, 3)]["fleet"][3] == 14
    assert [CELLS[c]["fleet"][0] for c in ((10, 90, 3), (25, 90, 3), (50, 90, 3), (100, 90, 3), (50, 90, 8), (50, 98, 8))] == [22, 0, 0, 0, 1, 30]
    assert [CELLS[(12, 90, 3)]["depot"][d][0] for d in (0, 1)] == [0.1, 4.4] and [CELLS[(12, 98, 3)]["depot"][d][0] for d in (0, 1)] == [5.2, 10.4] and [CELLS[(100, 90, 3)]["depot"][d][0] for d in (0, 1)] == [3.7, 4.8]
    assert all(CELLS[c]["depot"][1][0] > CELLS[c]["depot"][0][0] for c in CELLS)                      # in jeder Zelle ist die Ecke für den Sweep schlechter
    for needle in ("**67**", "**30**", "11,3 / 16,4 / 41,1 / 83,8 / 145,5 %", "4,4 / 9,0 / 28,2 / 65,8 / 129,4 %", "6,1 / 7,9 / 6,9 / 6,6 / 7,0 %", "1,3 / 2,3 / 1,3 / 2,9 / 4,5 %", "220 gegen 86 526"):
        assert needle in README, needle


def test_the_angular_order_as_route_and_as_giant_tour():
    assert [r1(_stats(n, f)["gaps"]["sw0_order"]["median"]) for n, f in ((10, 90), (12, 90), (25, 90), (50, 90), (100, 90))] == [11.3, 16.4, 41.1, 83.8, 145.5]
    assert [r1(_stats(n, f)["gaps"]["swb_order"]["median"]) for n, f in ((10, 90), (12, 90), (25, 90), (50, 90), (100, 90))] == [4.4, 9.0, 28.2, 68.3, 132.3]
    assert [r1(_stats(n, f)["gaps"]["splitb"]["median"]) for n, f in ((10, 90), (12, 90), (25, 90), (50, 90), (100, 90))] == [4.4, 9.0, 28.2, 65.8, 129.4]
    assert [r1(_stats(n, f)["gaps"]["es"]["median"]) for n, f in ((10, 90), (12, 90), (25, 90), (50, 90), (100, 90))] == [0.0, 0.6, 3.3, 8.3, 11.7]
    triples = []
    for n, f in ((10, 90), (12, 90), (25, 90), (50, 90), (100, 90)):
        rows = ev.band_rows(n, f)
        p = ev.paired([r["splitb"] for r in rows], [r["es"] for r in rows])
        triples.append((p["cheaper"], p["equal"], p["more"]))
    assert triples == [(9, 3, 68), (14, 2, 64), (2, 0, 30), (0, 0, 32), (0, 0, 32)]


def test_the_fair_comparison_row():
    for n, expected in ((25, 20), (50, 24)):
        rows = ev.band_rows(n, 90)
        assert sum(r["swb"] < r["sp1"] - C.TOL for r in rows) == expected
    for n, expected, diff in ((50, (16, 0, 16), None), (100, (17, 0, 15), -0.4)):
        rows = ev.band_rows(n, 90)
        p = ev.paired([r["swb"] for r in rows], [r["lam9_r"] for r in rows])
        assert (p["cheaper"], p["equal"], p["more"]) == expected and (diff is None or r1(p["median_diff"]) == diff)
    assert [r1(_stats(50, 90, 8)["gaps"][k]["median"]) for k in ("sw0", "swb")] == [14.8, 9.9] and [r1(_stats(12, 90)["vs"]["swb"]["median_diff"])] == [1.7]


# ----------------------------------------------------------------------------------------------------------------------------------- Handinstanz, Voreinstellung, Presets

def test_corner_hand_instance_numbers_of_the_readme(corner):
    assert round(W.sweep_plan(corner).cost, 2) == 93.73 and round(W.best_start(corner)[0].cost, 2) == 91.54 and round(A.split(corner, W.angular_order(corner)).cost, 2) == 104.26
    assert round(A.exact_cvrp(corner).cost, 2) == 77.79 and W.angular_order(corner) == (4, 5, 1, 2, 6, 3) and W.sweep_clusters(corner) == ((4, 5, 1, 2), (6, 3))
    assert ev.pct(ev.gap_percent(93.7339, 77.7889)) == "20,5 %" and ev.pct(ev.gap_percent(91.5437, 77.7889)) == "17,7 %"
    for text in ("93,73", "91,54", "104,26", "77,79", "(2 6 1 4)", "(3 5)", "{4, 5, 1, 2} und {6, 3}"):
        assert text in README


def test_default_setting_numbers_of_the_readme():
    a = ev.analyse(ev.Settings())
    assert {k: ev.de(p.cost) for k, p in a.plans.items()} == {"sw0_order": "538,21", "sw0": "517,11", "swb_order": "513,27", "swb": "492,17", "splitb": "513,27", "cut": "492,17", "sp1": "459,10", "sp1_r": "459,10",
                                                              "lam9_r": "459,10", "es": "444,40", "es_r": "444,40"}
    assert ev.de(a.exact.cost) == "444,40" and not a.opt_sweep and a.starts[0]["clusters"] == 4 and a.min_routes == 3
    assert all(t in README for t in ("444,40", "517,11", "492,17", "459,10"))


def test_preset_help_numbers():
    expected = {
        "Das Optimum ist keine Sweep-Zerlegung (n = 8)": ("444,40", "517,11", "+16,4 %", "492,17", "+10,8 %"),
        "Ein Kunde nahe am Depot sprengt den Keil (n = 6)": ("77,79", "(2 6 1 4)", "(3 5)", "93,73", "+20,5 %", "91,54", "+17,7 %"),
        "Der Start entscheidet (n = 8, Depot in der Ecke)": ("703,27", "4 statt 3", "843,89", "+20,0 %", "16 Starts", "29,4 %"),
        "Die Winkelfolge allein trifft das Optimum (n = 8)": ("380,72", "3,3 %"),
        "Enge Kapazität: mehr Routen als nötig (n = 12, 98 %)": ("4 statt der Mindestroutenzahl 3", "16 von 24", "13,3 %", "10,7 %", "447,47"),
    }
    assert set(expected) == set(C.PRESETS)
    for name, words in expected.items():
        for w in words:
            assert w in C.PRESET_HELP[name], (name, w)
    facts = {}
    for name, p in C.PRESETS.items():
        a = ev.analyse(ev.Settings(p["n"], p["family"], p["depot"], p["routes"], p["fill"], p["seed"]))
        costs = [r["cost"] for r in a.starts]
        facts[name] = (ev.de(a.exact.cost), {k: ev.pct(ev.gap_percent(pl.cost, a.exact.cost)) for k, pl in a.plans.items()}, {k: ev.de(pl.cost) for k, pl in a.plans.items()}, a.opt_sweep,
                       a.starts[0]["clusters"], a.min_routes, sum(r["clusters"] > a.min_routes for r in a.starts), len(costs), ev.pct(ev.gap_percent(max(costs), a.exact.cost)))
    f = facts["Das Optimum ist keine Sweep-Zerlegung (n = 8)"]
    assert f[0] == "444,40" and not f[3] and f[2]["sw0"] == "517,11" and f[1]["sw0"] == "16,4 %" and f[2]["swb"] == f[2]["cut"] == "492,17" and f[1]["swb"] == "10,8 %" and f[1]["es"] == "0,0 %"
    f = facts["Ein Kunde nahe am Depot sprengt den Keil (n = 6)"]
    assert f[0] == "77,79" and not f[3] and f[2]["sw0"] == "93,73" and f[1]["sw0"] == "20,5 %" and f[2]["swb"] == "91,54" and f[1]["swb"] == "17,7 %" and f[1]["sp1"] == f[1]["es"] == "0,0 %"
    f = facts["Der Start entscheidet (n = 8, Depot in der Ecke)"]
    assert f[0] == "703,27" and f[3] and f[4] == 4 and f[5] == 3 and f[2]["sw0"] == "843,89" and f[1]["sw0"] == "20,0 %" and f[1]["swb"] == "0,0 %" and f[7] == 16 and f[8] == "29,4 %" and f[1]["sp1_r"] == "0,0 %"
    f = facts["Die Winkelfolge allein trifft das Optimum (n = 8)"]
    assert f[0] == "380,72" and f[3] and f[1]["sw0_order"] == "0,0 %" and f[1]["sw0"] == "0,0 %" and f[1]["swb"] == "0,0 %" and f[1]["sp1"] == "3,3 %"
    f = facts["Enge Kapazität: mehr Routen als nötig (n = 12, 98 %)"]
    assert f[0] == "447,47" and f[4] == 4 and f[5] == 3 and f[6] == 16 and f[7] == 24 and f[1]["sw0"] == "13,3 %" and f[1]["swb"] == "10,7 %" and f[1]["es"] == "0,0 %"
