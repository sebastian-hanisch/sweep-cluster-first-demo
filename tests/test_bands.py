"""Vorberechnete Bänder (swp_bands.json): Aufbau, Vollständigkeit, Stimmigkeit der Zeilen und frische Nachrechnung einzelner Zeilen (Stichprobe)."""

import json
from pathlib import Path

import pytest

import swp_constants as C
import swp_evaluation as ev
import swp_sweep as W
from swp_scenario import make_instance

DATA = json.loads((Path(__file__).resolve().parent.parent / C.BAND_FILE).read_text(encoding="utf-8"))
BASE_KEYS = {"seed", "m", "ref", "es", "sp1", "lam9", "sw0_k", "sw0_order", "sw0", "swb_order", "swb", "swb_over_m", "splitb", "sp1_r", "lam9_r"}
EXPECTED = ({(3, n, f) for n in C.BAND_SIZES for f in C.BAND_FILLS[n]}) | {(C.SHORT_ROUTES, C.SHORT_N, f) for f in C.SHORT_FILLS}


def _cells():
    return DATA["cells"]


def _keys_for(n):
    keys = set(BASE_KEYS)
    if n <= C.CUT_MAX_N:
        keys.add("cut")
    if n <= C.ES_R_MAX_N:
        keys.add("es_r")
    if n <= C.N_MAX:
        keys |= {"opt_is_sweep", "k_opt"}
    return keys


def test_every_expected_cell_is_there_exactly_once():
    seen = [(c["routes"], c["n"], c["fill"]) for c in _cells() if (c["family"], c["depot"]) == C.BAND_CELLS[0]]
    assert sorted(seen) == sorted(EXPECTED) and len(seen) == len(set(seen))
    assert len(_cells()) == len(EXPECTED) * len(C.BAND_CELLS) == 40
    for c in _cells():
        assert [r["seed"] for r in c["rows"]] == list(C.BAND_SEEDS[c["n"]]) and (c["family"], c["depot"]) in C.BAND_CELLS


def test_every_row_has_exactly_the_expected_fields():
    for c in _cells():
        for r in c["rows"]:
            assert set(r) == _keys_for(c["n"]), (c["n"], c["fill"], r["seed"])


def test_rows_are_consistent():
    for c in _cells():
        for r in c["rows"]:
            tol = 1e-9
            assert r["sw0"] <= r["sw0_order"] + tol and r["swb"] <= r["swb_order"] + tol and r["swb"] <= r["sw0"] + tol and r["swb_order"] <= r["sw0_order"] + tol
            assert r["sp1_r"] <= r["sp1"] + tol and r["lam9_r"] <= r["sp1_r"] + tol and r["lam9"] <= r["sp1"] + tol and (c["n"] > C.ES_R_MAX_N or r["es_r"] <= r["es"] + tol)
            assert r["sw0_k"] >= r["m"] and 0.0 <= r["swb_over_m"] <= 1.0 and r["splitb"] > 0
            if "cut" in r:
                assert r["cut"] <= r["swb"] + tol and r["cut"] > 0
            if c["n"] in C.EXACT_SIZES:
                for key in ("sw0", "swb", "splitb", "cut", "sp1_r", "lam9_r", "es_r", "sp1", "es"):
                    assert r[key] >= r["ref"] - tol, (c["n"], c["fill"], r["seed"], key)               # kein Plan unter dem exakten Optimum
                assert r["k_opt"] >= r["m"] and isinstance(r["opt_is_sweep"], bool)


def test_references_are_the_same_in_every_cell_of_a_group_of_instances():
    for c in _cells():
        assert all(r["ref"] > 0 for r in c["rows"])


@pytest.mark.parametrize("n,fill,routes", [(10, 90, 3), (12, 98, 3), (25, 90, 3), (50, 98, 8)])
def test_a_fresh_recomputation_of_one_row_per_cell_matches(n, fill, routes):
    for c in (x for x in _cells() if x["n"] == n and x["fill"] == fill and x["routes"] == routes):
        row = c["rows"][0]
        fresh = ev.instance_row(n, c["family"], c["depot"], routes, row["seed"], fill, row["ref"], row["es"], row["sp1"], row["lam9"])
        assert set(fresh) == set(row)
        for key, value in row.items():
            if isinstance(value, float):
                assert fresh[key] == pytest.approx(value), (n, fill, c["family"], c["depot"], key)
            else:
                assert fresh[key] == value, (n, fill, c["family"], c["depot"], key)


def test_n100_rows_agree_with_a_fresh_fixed_start_sweep():
    for c in (x for x in _cells() if x["n"] == 100):
        row = c["rows"][-1]
        inst = make_instance(100, c["family"], c["depot"], 3, row["seed"], 90)
        clusters = W.sweep_clusters(inst, 0, 1)
        assert len(clusters) == row["sw0_k"] and W.in_order(inst, clusters).cost == pytest.approx(row["sw0_order"]) and W.with_routing(inst, clusters).cost == pytest.approx(row["sw0"])
        assert inst.min_routes == row["m"]


def test_the_stored_starts_step_is_documented():
    assert DATA["meta"]["start_step"] == {"100": 5} and DATA["meta"]["exact_max"] == 12


def test_statistics_helpers_on_small_data():
    rows = [{"family": 1, "depot": 0, "ref": 10.0, "sw0_k": 4, "m": 3, "swb_over_m": 0.5, "opt_is_sweep": True, "k_opt": 3, **{k: 10.0 for k in C.STRATEGY_KEYS}},
            {"family": 2, "depot": 1, "ref": 10.0, "sw0_k": 3, "m": 3, "swb_over_m": 0.0, "opt_is_sweep": False, "k_opt": 4, **{k: 10.0 for k in C.STRATEGY_KEYS}}]
    rows[1]["swb"] = 12.0
    rows[1]["sw0_order"] = 15.0
    rows[1]["sw0"] = 12.0
    rows[1]["cut"] = 11.0
    stats = ev.band_stats(rows)
    assert stats["count"] == 2 and stats["over_m"] == 1 and stats["over_m_share"] == 0.25 and stats["opt_is_sweep"] == 1 and stats["opt_over_m"] == 1
    assert stats["gaps"]["swb"]["median"] == pytest.approx(10.0) and stats["gaps"]["swb"]["hit"] == 1 and stats["by_depot"][1]["swb"] == pytest.approx(20.0) and stats["by_depot"][0]["swb"] == 0.0
    assert (stats["vs"]["swb"]["cheaper"], stats["vs"]["swb"]["equal"], stats["vs"]["swb"]["more"]) == (0, 1, 1)
    assert stats["cut_loss"] == pytest.approx(median_of([0.0, 100 * (12.0 - 11.0) / 11.0])) and stats["routing_loss"] == pytest.approx(median_of([0.0, 100 * 3.0 / 12.0]))
    assert ev.band_stats([]) == {} and ev.paired([], []) ["count"] == 0


def median_of(values):
    from statistics import median
    return median(values)
