"""Orakel-Tests sweep-cluster-first-demo: Winkelfolge, Füllen, Rundreise je Cluster, Schnittoptimum und Zählformeln gegen unabhängige Rechenwege (ORACLE-PLAYBOOK §2).

- Winkelfolge: eigene Sortierung mit math.atan2 und Listen.
- Füllen: eigene Schleife.
- Rundreise je Cluster: Aufzählung aller Reihenfolgen (bis 7 Kunden); die Heuristik nie unter der exakten Länge.
- Schnittoptimum: Aufzählung aller Zerlegungen der zyklischen Folge in zusammenhängende Stücke (jede Wahl von k Lücken), Rundreise je Stück durch Aufzählung.
- Zählformeln: Aufzählung der Zerlegungen eines Kreises beziehungsweise aller Zerlegungen einer Menge.
- Dominanz: Minimum über alle Reihenfolgen von Split gleich dem Optimum.
Nur Familien mit stetigen Koordinaten (1 und 2), weil bei ganzzahligen Koordinaten Winkelgleichstände von Rundungsfehlern abhängen. Mini-Instanzen mit festen Seeds."""

import itertools
import math

import numpy as np
import pytest

import swp_algorithm as A
import swp_sweep as W
from swp_scenario import make_instance

CELLS = [(f, d, r) for f in (1, 2) for d in (0, 1) for r in (2, 3)]


def _dist(inst, a, b):
    (xa, ya), (xb, yb) = inst.xy[a], inst.xy[b]
    return math.hypot(xa - xb, ya - yb)


def _route(inst, customers):
    path = (0, *customers, 0)
    return sum(_dist(inst, u, v) for u, v in zip(path, path[1:]))


def _tour(inst, cluster):
    return min(_route(inst, p) for p in itertools.permutations(cluster))


def _angular(inst):
    def key(c):
        dx, dy = inst.xy[c][0] - inst.xy[0][0], inst.xy[c][1] - inst.xy[0][1]
        ang = math.atan2(dy, dx)
        if ang < 0:
            ang += 2 * math.pi
        return (ang, math.hypot(dx, dy), c)

    return sorted(range(1, inst.n + 1), key=key)


def _fill(inst, order):
    out, cur, load = [], [], 0
    for c in order:
        if cur and load + inst.demand[c - 1] > inst.capacity:
            out.append(cur)
            cur, load = [], 0
        cur.append(c)
        load += inst.demand[c - 1]
    return out + ([cur] if cur else [])


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_angular_order_and_filling_match_the_independent_versions(family, depot, routes):
    for seed in range(8):
        inst = make_instance(6 + seed, family, depot, routes, seed, 60 + 5 * seed)
        order = _angular(inst)
        assert list(W.angular_order(inst)) == order
        for k in range(inst.n):
            for direction in (1, -1):
                rot = order[k:] + order[:k]
                rot = rot if direction == 1 else [rot[0]] + rot[1:][::-1]
                assert [list(c) for c in W.sweep_clusters(inst, k, direction)] == _fill(inst, rot), (seed, k, direction)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_exact_cluster_tours_match_the_enumeration(family, depot, routes):
    for seed in range(6):
        inst = make_instance(8, family, depot, routes, seed)
        rng = np.random.default_rng(seed)
        for size in (1, 2, 3, 5, 7):
            cluster = [int(c) + 1 for c in rng.permutation(8)[:size]]
            length, order = W.tsp_exact(inst, cluster)
            assert length == pytest.approx(_tour(inst, cluster)) and sorted(order) == sorted(cluster) and _route(inst, order) == pytest.approx(length)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_the_heuristic_is_never_below_the_exact_tour_and_stays_close(family, depot, routes):
    worse = total = 0
    for seed in range(6):
        inst = make_instance(12, family, depot, routes, seed)
        rng = np.random.default_rng(seed)
        for size in (6, 9, 12):
            cluster = [int(c) + 1 for c in rng.permutation(12)[:size]]
            exact = W.tsp_exact(inst, cluster)[0]
            heur, order = W.tsp_heuristic(inst, cluster, sorted(cluster, key=lambda c: W.angle_of(inst, c)))
            assert heur >= exact - 1e-9 and sorted(order) == sorted(cluster) and heur <= exact * 1.15
            worse += heur > exact + 1e-9
            total += 1
    assert worse <= total // 3                                                                 # meistens trifft die Heuristik die kürzeste Rundreise


def _cyclic_partitions(n, k):
    """Alle Zerlegungen der Positionen 0..n-1 eines Kreises in k zusammenhängende Stücke, als Menge von Mengen: k der n Lücken wählen."""
    if k == 1:
        return {frozenset([frozenset(range(n))])}
    out = set()
    for cuts in itertools.combinations(range(n), k):                        # Lücke i liegt zwischen Position i und i + 1
        blocks = []
        for a, b in zip(cuts, cuts[1:] + (cuts[0] + n,)):
            blocks.append(frozenset(p % n for p in range(a + 1, b + 1)))
        out.add(frozenset(blocks))
    return out


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
def test_the_number_of_sweep_partitions_matches_the_enumeration(n):
    for k in range(1, n + 1):
        assert len(_cyclic_partitions(n, k)) == W.n_sweep_partitions(n, k), (n, k)


def _set_partitions(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in _set_partitions(rest):
        yield [[first]] + part
        for i in range(len(part)):
            yield part[:i] + [[first] + part[i]] + part[i + 1:]


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 7, 8])
def test_the_stirling_numbers_match_the_enumeration(n):
    counts = {}
    for part in _set_partitions(list(range(n))):
        counts[len(part)] = counts.get(len(part), 0) + 1
    assert all(W.stirling2(n, k) == counts.get(k, 0) for k in range(0, n + 2))


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_the_cut_optimum_matches_the_enumeration_of_all_cyclic_partitions(family, depot, routes):
    for seed in range(4):
        inst = make_instance(7, family, depot, routes, seed, 70 + 7 * seed)
        order = _angular(inst)
        best = math.inf
        for k in range(1, inst.n + 1):
            for part in _cyclic_partitions(inst.n, k):
                clusters = [[order[p] for p in block] for block in part]
                if all(sum(inst.demand[c - 1] for c in cl) <= inst.capacity for cl in clusters):
                    best = min(best, sum(_tour(inst, cl) for cl in clusters))
        got = W.cut_optimal(inst)
        assert got.cost == pytest.approx(best) and A.is_feasible_plan(inst, got.routes) and A.plan_length(inst, got.routes) == pytest.approx(got.cost)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_is_sweep_partition_matches_a_direct_check(family, depot, routes):
    for seed in range(4):
        inst = make_instance(8, family, depot, routes, seed)
        order = _angular(inst)
        rng = np.random.default_rng(seed)
        for _ in range(30):
            size = int(rng.integers(1, 7))
            cluster = [int(c) + 1 for c in rng.permutation(8)[:size]]
            pos = sorted(order.index(c) for c in cluster)
            direct = any(sorted((s + i) % 8 for i in range(size)) == pos for s in range(8)) or size == 8
            assert W.is_sweep_partition(inst, [cluster]) == direct, (cluster, pos)


@pytest.mark.parametrize("family,depot,routes", CELLS[::2])
def test_dominance_the_best_split_over_all_orders_is_the_optimum(family, depot, routes):
    for seed in range(3):
        inst = make_instance(6, family, depot, routes, seed, 80 + 8 * seed)
        best = min(A.split(inst, p).cost for p in itertools.permutations(range(1, 7)))
        assert best == pytest.approx(A.exact_cvrp(inst).cost)
