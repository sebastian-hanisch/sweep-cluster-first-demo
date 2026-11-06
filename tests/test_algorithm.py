"""Sweep, Rundreise je Cluster, Schnittoptimum und Vergleich an der Handinstanz (PLAN-06): jede Zahl ist hier von Hand aus Wurzeln zusammengesetzt.

Handinstanz (conftest.py `corner`): Depot (0,0) in der Ecke; Kunden 1 (15,14), 2 (13,14), 3 (1,13), 4 (16,4), 5 (2,1), 6 (13,16); Nachfragen 3, 3, 4, 1, 4, 4; Kapazität 11; Optimum 77,79."""

import math

import pytest

import swp_algorithm as A
import swp_construct as K
import swp_evaluation as ev
import swp_savings as S
import swp_sweep as W
from conftest import OPTIMUM, TOUR_LENGTH
from swp_scenario import make_instance

ROUND2 = 0.005
S5, S205, S101, S425, S153, S170, S365 = (math.sqrt(v) for v in (5, 205, 101, 425, 153, 170, 365))

# (Startposition, Richtung) -> (Cluster, Kosten mit Winkelfolge, Kosten mit Rundreise)
VARIANTS = {
    (0, 1): (((4, 5, 1, 2), (6, 3)), 116.32, 93.73),
    (0, -1): (((4, 3, 6), (2, 1, 5)), 108.70, 96.00),
    (1, 1): (((5, 1, 2), (6, 3, 4)), 108.70, 96.00),
    (1, -1): (((5, 4, 3), (6, 2, 1)), 92.22, 91.54),
    (2, 1): (((1, 2, 6), (3, 4, 5)), 92.22, 91.54),
    (2, -1): (((1, 5, 4), (3, 6, 2)), 116.23, 93.63),
    (3, 1): (((2, 6, 3), (4, 5, 1)), 116.23, 93.63),
    (3, -1): (((2, 1, 5, 4), (3, 6)), 116.32, 93.73),
    (4, 1): (((6, 3, 4), (5, 1, 2)), 108.70, 96.00),
    (4, -1): (((6, 2, 1), (5, 4, 3)), 92.22, 91.54),
    (5, 1): (((3, 4, 5), (1, 2, 6)), 92.22, 91.54),
    (5, -1): (((3, 6, 2), (1, 5, 4)), 116.23, 93.63),
}


def test_the_corner_instance_is_the_generator_instance(corner):
    assert make_instance(6, 0, 1, 2, 13, 90) == corner and corner.min_routes == 2 and A.exact_cvrp(corner).cost == pytest.approx(77.79, abs=ROUND2)


def test_angles_by_hand(corner):
    expected = {4: math.atan(4 / 16), 5: math.atan(1 / 2), 1: math.atan(14 / 15), 2: math.atan(14 / 13), 6: math.atan(16 / 13), 3: math.atan(13 / 1)}
    for c, angle in expected.items():
        assert W.angle_of(corner, c) == pytest.approx(angle)
    assert [round(math.degrees(W.angle_of(corner, c)), 2) for c in (4, 5, 1, 2, 6, 3)] == [14.04, 26.57, 43.03, 47.12, 50.91, 85.60]
    assert W.angular_order(corner) == (4, 5, 1, 2, 6, 3)


def test_rotation_and_filling_by_hand(corner):
    order = W.angular_order(corner)
    assert W.rotated(order, 0, 1) == (4, 5, 1, 2, 6, 3) and W.rotated(order, 2, 1) == (1, 2, 6, 3, 4, 5)
    assert W.rotated(order, 2, -1) == (1, 5, 4, 3, 6, 2) and W.rotated(order, 0, -1) == (4, 3, 6, 2, 1, 5)          # Startkunde vorn, der Rest rückwärts
    assert W.fill_until_full(corner, (4, 5, 1, 2, 6, 3)) == ((4, 5, 1, 2), (6, 3))                                  # 1 + 4 + 3 + 3 = 11, dann passt 6 (4) nicht mehr
    assert [corner.load(c) for c in W.fill_until_full(corner, (4, 5, 1, 2, 6, 3))] == [11, 8]


@pytest.mark.parametrize("start", list(VARIANTS))
def test_all_twelve_sweep_variants_by_hand(corner, start):
    k, direction = start
    clusters, cost_order, cost_route = VARIANTS[start]
    assert W.sweep_clusters(corner, k, direction) == clusters
    assert W.sweep_plan(corner, k, direction, False).cost == pytest.approx(cost_order, abs=ROUND2)
    assert W.sweep_plan(corner, k, direction, True).cost == pytest.approx(cost_route, abs=ROUND2)


def test_a_cluster_route_from_square_roots(corner):
    """Cluster (4 5 1 2): Rundreise Depot 5 4 1 2 Depot = sqrt5 + sqrt205 + sqrt101 + 2 + sqrt365; Cluster (6 3): Depot 6 3 Depot = sqrt425 + sqrt153 + sqrt170."""
    length, order = W.tsp_exact(corner, (4, 5, 1, 2))
    assert length == pytest.approx(S5 + S205 + S101 + 2 + S365) and order in ((5, 4, 1, 2), (2, 1, 4, 5))
    length, order = W.tsp_exact(corner, (6, 3))
    assert length == pytest.approx(S425 + S153 + S170) and order in ((6, 3), (3, 6))
    assert W.sweep_plan(corner, 0, 1, True).cost == pytest.approx(S5 + S205 + S101 + 2 + S365 + S425 + S153 + S170)


def test_best_start_and_the_split_of_the_angular_order_by_hand(corner):
    plan, k, direction = W.best_start(corner, True)
    assert plan.cost == pytest.approx(91.54, abs=ROUND2) and (k, direction) == (1, -1)                              # erster der billigsten Starts
    assert W.best_start(corner, False)[0].cost == pytest.approx(92.22, abs=ROUND2)
    split = A.split(corner, W.angular_order(corner))
    assert split.cost == pytest.approx(104.26, abs=ROUND2) and split.routes == ((4, 5), (1, 2, 6), (3,))
    assert W.split_best_start(corner).cost == pytest.approx(92.22, abs=ROUND2)


def test_the_cut_optimum_equals_the_best_start_here_and_misses_the_optimum(corner):
    cut = W.cut_optimal(corner)
    assert cut.cost == pytest.approx(91.54, abs=ROUND2) and A.is_feasible_plan(corner, cut.routes)
    assert A.exact_cvrp(corner).cost == pytest.approx(77.79, abs=ROUND2)


def test_the_optimum_is_not_a_sweep_partition_by_hand(corner):
    ex = A.exact_cvrp(corner)
    assert sorted(map(sorted, ex.routes)) == [[1, 2, 4, 6], [3, 5]]
    assert W.route_blocks(corner, (2, 6, 1, 4)) == 2 and W.route_blocks(corner, (3, 5)) == 2                       # Folge 4 5 1 2 6 3: {1,2,4,6} sind {4} und {1 2 6}, {3,5} sind {5} und {3}
    assert not W.is_sweep_partition(corner, ex.routes)
    assert W.is_sweep_partition(corner, ((4, 5), (1, 2, 6), (3,))) and W.is_sweep_partition(corner, ((3, 4, 5), (1, 2, 6)))
    arcs = W.route_arcs(corner, ((1, 2, 6), (3, 4, 5)))
    assert arcs[0]["contiguous"] and round(arcs[0]["from_deg"], 1) == 43.0 and round(arcs[0]["to_deg"], 1) == 50.9
    assert arcs[1]["contiguous"] and round(arcs[1]["from_deg"], 1) == 85.6 and round(arcs[1]["to_deg"], 1) == 26.6   # über den Nullwinkel hinweg


def test_savings_and_insertion_hit_the_optimum_here_with_and_without_the_tour_step(corner):
    assert A.plan_length(corner, S.savings_routes(corner)) == pytest.approx(77.79, abs=ROUND2)
    assert W.reoptimize(corner, S.savings_routes(corner)).cost == pytest.approx(77.79, abs=ROUND2)
    es = A.split(corner, K.insert_split_order(corner))
    assert es.cost == pytest.approx(77.79, abs=ROUND2) and W.reoptimize(corner, es.routes).cost == pytest.approx(77.79, abs=ROUND2)


def test_the_analysis_of_the_corner_instance_matches_the_hand_numbers(corner, monkeypatch):
    monkeypatch.setattr(ev, "build_instance", lambda settings: corner)
    a = ev.analyse(ev.Settings(6, 0, 1, 2, 90, 13))
    assert {k: round(p.cost, 2) for k, p in a.plans.items()} == {"sw0_order": 116.32, "sw0": 93.73, "swb_order": 92.22, "swb": 91.54, "splitb": 92.22, "cut": 91.54, "sp1": 77.79, "sp1_r": 77.79,
                                                                  "lam9_r": 77.79, "es": 77.79, "es_r": 77.79}
    assert len(a.starts) == 12 and len({round(r["cost"], 6) for r in a.starts}) == 4 and not a.opt_sweep


def test_counting_formulas():
    assert [W.n_sweep_partitions(6, k) for k in range(1, 7)] == [1, 15, 20, 15, 6, 1]
    assert [W.stirling2(6, k) for k in range(1, 7)] == [1, 31, 90, 65, 15, 1] and W.stirling2(12, 3) == 86526 and W.n_sweep_partitions(12, 3) == 220
    assert W.n_sweep_partitions(5, 0) == 0 and W.n_sweep_partitions(5, 6) == 0 and W.stirling2(0, 0) == 1 and W.stirling2(3, 4) == 0


def test_kernel_split_exact_and_tour_from_earlier_pieces(hand):
    assert A.exact_cvrp(hand).cost == pytest.approx(OPTIMUM)
    length, order = A.tsp_tour(hand)
    assert length == pytest.approx(TOUR_LENGTH) and order == (2, 6, 3, 4, 1, 5)
    assert A.split(hand, (1, 4, 2, 6, 3, 5)).routes == ((1, 4), (2, 6, 3, 5))
