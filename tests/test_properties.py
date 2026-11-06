"""Eigenschaftstests (ORACLE-PLAYBOOK §5, Schicht „Eigenschaften“): Aussagen, die für jede Instanz gelten, an vielen festen Seeds geprüft.

Stetige Koordinaten (Familien 1 und 2) für alles, was von Winkelgleichständen abhängt; Instanzen bis 12 Kunden, damit die Rundreise je Cluster exakt rechnet."""

import dataclasses
import math

import numpy as np
import pytest

import swp_algorithm as A
import swp_evaluation as ev
import swp_savings as S
import swp_sweep as W
from swp_scenario import Instance, make_instance

CONTINUOUS = [(f, d, r) for f in (1, 2) for d in (0, 1) for r in (2, 3)]


def _transformed(inst, f):
    return Instance(tuple(f(x, y) for x, y in inst.xy), inst.demand, inst.capacity)


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_every_start_gives_a_feasible_plan_and_the_counts_add_up(family, depot, routes):
    for seed in range(4):
        inst = make_instance(9 + seed, family, depot, routes, seed, 62 + 9 * seed)
        for item in W.all_starts(inst, True):
            plan = item["plan"]
            assert A.is_feasible_plan(inst, plan.routes) and plan.cost == pytest.approx(A.plan_length(inst, plan.routes)) and len(plan.routes) >= inst.min_routes
            clusters = W.sweep_clusters(inst, item["k"], item["direction"])
            assert sum(inst.load(c) for c in clusters) == sum(inst.demand) and len(clusters) == item["routes"]
            assert sorted(c for cl in clusters for c in cl) == list(range(1, inst.n + 1))


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_the_tour_step_is_never_worse_and_the_best_start_never_worse_than_any_start(family, depot, routes):
    for seed in range(4):
        inst = make_instance(10, family, depot, routes, seed, 80)
        order_costs = {(r["k"], r["direction"]): r["cost"] for r in W.all_starts(inst, False)}
        tour_costs = {(r["k"], r["direction"]): r["cost"] for r in W.all_starts(inst, True)}
        assert all(tour_costs[key] <= order_costs[key] + 1e-9 for key in tour_costs)
        assert W.best_start(inst, True)[0].cost == pytest.approx(min(tour_costs.values())) and W.best_start(inst, False)[0].cost == pytest.approx(min(order_costs.values()))
        assert W.sweep_plan(inst, 0, 1, True).cost == pytest.approx(tour_costs[(0, 1)])


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_the_cut_optimum_is_never_worse_than_any_sweep_and_never_better_than_the_optimum(family, depot, routes):
    for seed in range(4):
        inst = make_instance(9, family, depot, routes, seed, 75)
        cut = W.cut_optimal(inst)
        assert all(cut.cost <= r["cost"] + 1e-9 for r in W.all_starts(inst, True))
        assert cut.cost >= A.exact_cvrp(inst).cost - 1e-9 and W.split_best_start(inst).cost >= A.exact_cvrp(inst).cost - 1e-9


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_the_cut_optimum_is_a_sweep_partition(family, depot, routes):
    for seed in range(4):
        inst = make_instance(9, family, depot, routes, seed, 75)
        assert W.is_sweep_partition(inst, W.cut_optimal(inst).routes)


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_moving_scaling_turning_mirroring_and_renumbering_keep_the_cyclic_results(family, depot, routes):
    for seed in range(3):
        inst = make_instance(9, family, depot, routes, seed, 75)
        base = (W.best_start(inst, True)[0].cost, W.cut_optimal(inst).cost, W.split_best_start(inst).cost, W.best_start(inst, False)[0].cost)
        theta = math.radians(37)
        x0, y0 = inst.xy[0]
        variants = {
            "verschoben": _transformed(inst, lambda x, y: (x + 11.0, y - 7.0)),
            "gedreht": _transformed(inst, lambda x, y: (x0 + (x - x0) * math.cos(theta) - (y - y0) * math.sin(theta), y0 + (x - x0) * math.sin(theta) + (y - y0) * math.cos(theta))),
            "gespiegelt": _transformed(inst, lambda x, y: (x, 2 * y0 - y)),
        }
        for name, other in variants.items():
            got = (W.best_start(other, True)[0].cost, W.cut_optimal(other).cost, W.split_best_start(other).cost, W.best_start(other, False)[0].cost)
            assert got == pytest.approx(base, rel=1e-9), (seed, name)
        scaled = _transformed(inst, lambda x, y: (2 * x, 2 * y))
        assert W.best_start(scaled, True)[0].cost == pytest.approx(2 * base[0])
        rng = np.random.default_rng(seed)
        perm = [int(p) + 1 for p in rng.permutation(inst.n)]
        xy = [inst.xy[0]] + [None] * inst.n
        demand = [0] * inst.n
        for c in range(1, inst.n + 1):
            xy[perm[c - 1]] = inst.xy[c]
            demand[perm[c - 1] - 1] = inst.demand[c - 1]
        renamed = Instance(tuple(xy), tuple(demand), inst.capacity)
        assert W.best_start(renamed, True)[0].cost == pytest.approx(base[0]) and W.cut_optimal(renamed).cost == pytest.approx(base[1])


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_with_room_for_everyone_the_sweep_is_the_tour_through_all_customers(family, depot, routes):
    for seed in range(4):
        inst = dataclasses.replace(make_instance(10, family, depot, routes, seed), capacity=10 ** 6)
        assert W.sweep_clusters(inst, 3, -1) == (tuple(W.rotated(W.angular_order(inst), 3, -1)),)
        assert W.sweep_plan(inst, 0, 1, True).cost == pytest.approx(A.tsp_tour(inst)[0]) and W.cut_optimal(inst).cost == pytest.approx(A.tsp_tour(inst)[0])


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_reoptimizing_a_plan_never_makes_it_worse_and_keeps_the_customers_of_every_route(family, depot, routes):
    for seed in range(4):
        inst = make_instance(11, family, depot, routes, seed, 85)
        for plan in (S.savings_routes(inst), A.split(inst, W.angular_order(inst)).routes):
            new = W.reoptimize(inst, plan)
            assert new.cost <= A.plan_length(inst, plan) + 1e-9 and A.is_feasible_plan(inst, new.routes)
            assert sorted(map(sorted, new.routes)) == sorted(map(sorted, plan))


@pytest.mark.parametrize("family,depot,routes", CONTINUOUS)
def test_the_analysis_orders_the_strategies_by_construction(family, depot, routes):
    a = ev.analyse(ev.Settings(9, family, depot, routes, 80, 4))
    p = a.plans
    assert p["cut"].cost <= p["swb"].cost + 1e-9 <= p["sw0"].cost + 2e-9 and p["swb"].cost <= p["swb_order"].cost + 1e-9 and p["sw0"].cost <= p["sw0_order"].cost + 1e-9
    assert p["sp1_r"].cost <= p["sp1"].cost + 1e-9 and p["es_r"].cost <= p["es"].cost + 1e-9 and p["lam9_r"].cost <= p["sp1_r"].cost + 1e-9
    assert all(plan.cost >= a.exact.cost - 1e-9 and A.is_feasible_plan(a.inst, plan.routes) for plan in p.values())
    assert a.opt_sweep == W.is_sweep_partition(a.inst, a.exact.routes) and len(a.starts) == 2 * a.inst.n


def test_starts_are_ordered_and_a_step_thins_them_out():
    inst = make_instance(10, 1, 0, 3, 1)
    assert W.starts(inst) == [(k, d) for k in range(10) for d in (1, -1)] and W.starts(inst, 5) == [(0, 1), (0, -1), (5, 1), (5, -1)]
