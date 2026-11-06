"""Randfälle, an denen der Sweep erfahrungsgemäß bricht (DEMO-PLAYBOOK §12): n = 1 und n = 2, Kunde auf dem Depot, alle Kunden auf einem Strahl, Gleichstände im Winkel, Nachfrage gleich Kapazität,
Kapazität für alle, Depot in der Ecke, Cluster über der Grenze der exakten Rundreise, Reglergrenzen, Abstände an der Null."""

import dataclasses
import math

import pytest

import swp_algorithm as A
import swp_constants as C
import swp_evaluation as ev
import swp_sweep as W
from swp_scenario import Instance, make_instance


def test_one_customer():
    inst = Instance(((0.0, 0.0), (3.0, 4.0)), (2,), 2)
    assert W.angular_order(inst) == (1,) and W.sweep_clusters(inst, 0, 1) == ((1,),) and W.sweep_clusters(inst, 0, -1) == ((1,),)
    assert W.sweep_plan(inst).cost == pytest.approx(10.0) and W.sweep_plan(inst, routing=False).cost == pytest.approx(10.0)
    assert W.best_start(inst)[0].cost == pytest.approx(10.0) and W.cut_optimal(inst).cost == pytest.approx(10.0) and W.split_best_start(inst).cost == pytest.approx(10.0)
    assert W.is_sweep_partition(inst, [(1,)]) and W.route_arcs(inst, [(1,)])[0]["contiguous"] and W.reoptimize(inst, [(1,)]).cost == pytest.approx(10.0)


def test_exactly_two_customers():
    inst = Instance(((0.0, 0.0), (3.0, 4.0), (-3.0, 4.0)), (1, 1), 2)             # Winkel 53,13 und 126,87 Grad
    assert W.angular_order(inst) == (1, 2) and W.sweep_clusters(inst, 0, 1) == ((1, 2),) and W.sweep_clusters(inst, 1, 1) == ((2, 1),)
    assert W.sweep_plan(inst).cost == pytest.approx(5 + 6 + 5) and len(W.all_starts(inst)) == 4
    apart = dataclasses.replace(inst, capacity=1)
    assert W.sweep_clusters(apart, 0, 1) == ((1,), (2,)) and W.sweep_plan(apart).cost == pytest.approx(20.0)
    assert W.n_sweep_partitions(2, 2) == 1 and W.cut_optimal(apart).cost == pytest.approx(20.0)


def test_a_customer_on_the_depot_has_the_angle_zero_and_goes_first():
    inst = Instance(((5.0, 5.0), (5.0, 5.0), (9.0, 9.0), (1.0, 5.0)), (1, 1, 1), 3)
    assert W.angle_of(inst, 1) == 0.0 and W.angular_order(inst)[0] == 1
    assert W.sweep_plan(inst).cost == pytest.approx(A.exact_cvrp(inst).cost)       # die Rundreise durch alle Kunden


def test_customers_on_one_ray_are_ordered_by_distance_and_ties_by_number():
    inst = Instance(((0.0, 0.0), (3.0, 3.0), (1.0, 1.0), (2.0, 2.0), (1.0, 1.0)), (1, 1, 1, 1), 4)
    assert W.angular_order(inst) == (2, 4, 3, 1)                                  # gleicher Winkel 45 Grad: Abstand, dann Nummer (2 und 4 haben den gleichen Ort)
    assert sorted(W.sweep_clusters(inst, 0, 1)[0]) == [1, 2, 3, 4] and W.sweep_plan(inst).cost == pytest.approx(2 * math.hypot(3, 3))


def test_demand_equal_to_capacity_means_one_customer_per_route():
    inst = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0), (-3.0, 4.0)), (4, 4, 4), 4)
    assert all(len(c) == 1 for c in W.sweep_clusters(inst, 0, 1)) and len(W.sweep_clusters(inst, 0, 1)) == 3
    assert all(item["routes"] == 3 for item in W.all_starts(inst)) and W.cut_optimal(inst).cost == pytest.approx(2 * (5 + 10 + 5))


def test_capacity_for_everyone_is_one_cluster_for_every_start():
    inst = dataclasses.replace(make_instance(8, 1, 1, 2, 3), capacity=10 ** 6)
    assert all(len(W.sweep_clusters(inst, k, d)) == 1 for k, d in W.starts(inst))
    assert len({round(item["cost"], 9) for item in W.all_starts(inst, True)}) == 1       # eine Route: der Start spielt keine Rolle mehr


def test_depot_in_the_corner_keeps_all_angles_in_one_quadrant():
    for seed in range(6):
        inst = make_instance(10, 1, 1, 3, seed)
        assert all(0.0 <= W.angle_of(inst, c) <= math.pi / 2 for c in range(1, 11))


def test_a_cluster_over_the_exact_limit_uses_the_heuristic_and_the_exact_tour_refuses():
    inst = make_instance(14, 1, 0, 2, 4)
    big = dataclasses.replace(inst, capacity=10 ** 6)
    cluster = tuple(range(1, 15))
    with pytest.raises(ValueError):
        W.tsp_exact(big, cluster)
    length, order = W.route_of(big, cluster, W.angular_order(big))
    assert sorted(order) == list(cluster) and length == pytest.approx(A.route_length(big, order)) and length <= A.route_length(big, W.angular_order(big)) + 1e-9
    assert W.sweep_plan(big).cost == pytest.approx(length)
    assert len(W.route_of(big, cluster[:12])[1]) == 12                                           # genau 12 Kunden: noch exakt


def test_steps_for_a_hundred_customers_only_use_every_fifth_start():
    inst = make_instance(100, 1, 0, 3, 300000)
    assert len(W.starts(inst, C.BAND_START_STEP[100])) == 40 and W.starts(inst)[:2] == [(0, 1), (0, -1)]


def test_every_control_limit_gives_a_valid_analysis():
    for n in (C.N_MIN, C.N_MAX):
        for fill in (C.FILL_MIN, C.FILL_MAX):
            for routes in (C.ROUTES_MIN, C.ROUTES_MAX):
                for depot in (0, 1):
                    a = ev.analyse(ev.Settings(n, 2, depot, routes, fill, C.SEED_MAX))
                    assert all(p.cost >= a.exact.cost - 1e-9 and A.is_feasible_plan(a.inst, p.routes) for p in a.plans.values())
                    assert len(a.starts) == 2 * n and ev.verdict_compare(a)[1] and ev.verdict_starts(a)[1] and ev.verdict_losses(a)[1]
                    for k, d, routing in ((0, 1, True), (n - 1, -1, False)):
                        view = ev.sweep_view(a.settings, k, d, routing)
                        assert ev.verdict_sweep(a, k, d, routing, view)[1] and len(ev.boundary_angles(a.inst, view["order"], view["clusters"])) == len(view["clusters"]) - 1


def test_boundary_angles_lie_between_the_neighbouring_customers(corner):
    view = ev.sweep_view(ev.Settings(6, 0, 1, 2, 90, 13), 0, 1, True)
    assert view["clusters"] == ((4, 5, 1, 2), (6, 3))
    (boundary,) = ev.boundary_angles(corner, view["order"], view["clusters"])
    assert boundary == pytest.approx(math.radians((47.12 + 50.91) / 2), abs=0.01)


def test_helpers_at_their_edges():
    assert ev.gap_percent(10.0, 0.0) == 0.0 and ev.gap_percent(5.0 + 1e-12, 5.0) == 0.0 and ev.gap_percent(4.0, 5.0) == 0.0 and ev.gap_percent(11.0, 10.0) == pytest.approx(10.0)
    assert ev.diff_percent(5.0, 5.0 + 1e-12) == 0.0 and ev.diff_percent(11.0, 10.0) == pytest.approx(10.0) and ev.diff_percent(9.0, 10.0) == pytest.approx(-10.0) and ev.diff_percent(1.0, 0.0) == 0.0
    assert ev.signed_pct(-0.04) == "0,0 %" and ev.signed_pct(0.5) == "+0,5 %" and ev.signed_pct(-1.3) == "−1,3 %"
    assert ev.de(3.14159) == "3,14" and ev.routes_word(1) == "1 Route" and ev.routes_word(3) == "3 Routen" and ev.instances_word(1) == "1 Instanz" and ev.instances_word(32) == "32 Instanzen"
    assert ev.direction_text(1) == "gegen den Uhrzeigersinn" and ev.direction_text(-1) == "mit dem Uhrzeigersinn" and ev.pct(4.26) == "4,3 %"
