"""Sweep und Cluster-first (Stück 6 der Linie Tourenbildung).

Sweep (Gillett und Miller, 1974, nach Sekundärquellen): Die Kunden werden nach dem Polarwinkel um das Depot geordnet (Winkel von 0 bis 2π gegen den Uhrzeigersinn ab Osten; Gleichstand:
kleinerer Abstand zum Depot, dann kleinere Nummer; ein Kunde auf dem Depot hat per Setzung den Winkel 0). Die zyklische Winkelfolge wird bei einem Startkunden (Position k) geöffnet und in einer
der beiden Richtungen gelesen (+1: gegen den Uhrzeigersinn, -1: mit dem Uhrzeigersinn; bei -1 bleibt der Startkunde vorn und der Rest läuft rückwärts). „Füllen bis voll“ (Stück 3) schneidet die Folge in
Cluster: eine neue Route beginnt, sobald der nächste Kunde nicht mehr passt. Der feste Start ist der Kunde mit dem kleinsten Winkel (k = 0, Richtung +1).

Zweiter Schritt je Cluster (route-second): entweder die Reihenfolge der Winkelfolge oder die kürzeste Rundreise durch das Depot und alle Kunden des Clusters: exakt (Teilmengen-DP) bis EXACT_MAX Kunden,
darüber eine Heuristik (2-opt und Or-opt ab der Winkelfolge).

Schnittoptimum: die beste Zerlegung der zyklischen Winkelfolge in zusammenhängende Cluster, die Rundreise je Cluster eingerechnet (Dynamische Programmierung je Startposition und Richtung, die Kosten
der Cluster werden zwischengespeichert). Nach dem Namen entspricht das dem Petal-Verfahren mit Sektoren (Ryan, Hjorring und Glover, 1993; ungeprüft)."""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import swp_algorithm as A
from swp_scenario import Instance, distance_matrix

EXACT_MAX = 12                              # bis zu dieser Clustergröße rechnet die Rundreise exakt


@dataclass(frozen=True)
class Plan:
    cost: float
    routes: tuple[tuple[int, ...], ...]


# ----------------------------------------------------------------------------------------------------------------------------------------- Winkelfolge

def angle_of(inst: Instance, c: int) -> float:
    """Polarwinkel des Kunden c um das Depot in Bogenmaß (0 bis 2π), gegen den Uhrzeigersinn ab Osten; Kunde auf dem Depot: 0."""
    dx, dy = inst.xy[c][0] - inst.xy[0][0], inst.xy[c][1] - inst.xy[0][1]
    return math.atan2(dy, dx) % (2 * math.pi) if (dx or dy) else 0.0


def angular_order(inst: Instance) -> tuple[int, ...]:
    """Die Kunden nach Winkel, Gleichstand: Abstand, dann Nummer."""
    D = distance_matrix(inst)
    return tuple(sorted(range(1, inst.n + 1), key=lambda c: (angle_of(inst, c), float(D[0][c]), c)))


def rotated(order, k: int, direction: int) -> tuple[int, ...]:
    """Die zyklische Folge ab Position k; Richtung -1: der Startkunde bleibt vorn, der Rest läuft rückwärts."""
    base = tuple(order[k:]) + tuple(order[:k])
    return base if direction > 0 else (base[0],) + base[1:][::-1]


def fill_until_full(inst: Instance, order) -> tuple[tuple[int, ...], ...]:
    """Cluster durch „Füllen bis voll“: eine neue Route beginnt, sobald der nächste Kunde nicht mehr passt (kein Blick auf Entfernungen)."""
    clusters, current, load = [], [], 0
    for c in order:
        q = inst.demand[c - 1]
        if current and load + q > inst.capacity:
            clusters.append(tuple(current))
            current, load = [], 0
        current.append(c)
        load += q
    if current:
        clusters.append(tuple(current))
    return tuple(clusters)


def sweep_clusters(inst: Instance, k: int = 0, direction: int = 1) -> tuple[tuple[int, ...], ...]:
    return fill_until_full(inst, rotated(angular_order(inst), k, direction))


# ----------------------------------------------------------------------------------------------------------------------------------------- Rundreise je Cluster

def tour_length(inst: Instance, route) -> float:
    return A.route_length(inst, route)


@lru_cache(maxsize=200_000)
def _tsp_exact(inst: Instance, nodes: tuple[int, ...]) -> tuple[float, tuple[int, ...]]:
    D = distance_matrix(inst)
    k = len(nodes)
    if k == 1:
        return float(2 * D[0][nodes[0]]), (nodes[0],)
    d = np.array([[D[a][b] for b in nodes] for a in nodes])
    d0 = np.array([D[0][a] for a in nodes])
    size = 1 << k
    dp = np.full((size, k), np.inf)
    parent = np.full((size, k), -1, dtype=int)
    for i in range(k):
        dp[1 << i, i] = d0[i]
    for mask in range(1, size):
        cand = dp[mask][:, None] + d
        vals, args = cand.min(axis=0), cand.argmin(axis=0)
        for nxt in range(k):
            if mask >> nxt & 1 or vals[nxt] == np.inf:
                continue
            nm = mask | (1 << nxt)
            if vals[nxt] < dp[nm, nxt] - 1e-12:
                dp[nm, nxt] = vals[nxt]
                parent[nm, nxt] = args[nxt]
    full = size - 1
    total = dp[full] + d0
    last = int(np.argmin(total))
    best = float(total[last])
    order, mask = [], full
    while last != -1:
        order.append(nodes[last])
        prev = int(parent[mask, last])
        mask ^= 1 << last
        last = prev
    return best, tuple(order[::-1])


def tsp_exact(inst: Instance, cluster) -> tuple[float, tuple[int, ...]]:
    """Kürzeste Rundreise Depot - Kunden - Depot durch alle Kunden des Clusters (Teilmengen-DP; höchstens EXACT_MAX Kunden). Gleichstand: bestimmt die Rechnung, nicht die Eingabereihenfolge."""
    if len(cluster) > EXACT_MAX:
        raise ValueError(f"mehr als {EXACT_MAX} Kunden")
    return _tsp_exact(inst, tuple(sorted(cluster)))


def tsp_heuristic(inst: Instance, cluster, start_order=None) -> tuple[float, tuple[int, ...]]:
    """2-opt und Or-opt (Segmente bis 3, beide Richtungen) ab der Folge `start_order` (Voreinstellung: die Reihenfolge von `cluster`), bis keine Verbesserung mehr gefunden wird. Eine Heuristik: die Länge liegt nie unter der Rundreise."""
    D = distance_matrix(inst)
    route = list(start_order if start_order is not None else cluster)
    n = len(route)
    if n <= 2:
        return float(tour_length(inst, route)), tuple(route)
    improved = True
    while improved:
        improved = False
        path = [0] + route + [0]
        for i in range(1, n):
            for j in range(i + 1, n + 1):
                a, b, c, d = path[i - 1], path[i], path[j], path[j + 1]
                if D[a][c] + D[b][d] < D[a][b] + D[c][d] - 1e-10:
                    path[i:j + 1] = path[i:j + 1][::-1]
                    improved = True
        route = path[1:-1]
        for seg in (1, 2, 3):
            for i in range(n - seg + 1):
                moved = route[i:i + seg]
                rest = route[:i] + route[i + seg:]
                best = (tour_length(inst, route), None)
                for p in range(len(rest) + 1):
                    for cand in (moved, moved[::-1]):
                        trial = rest[:p] + cand + rest[p:]
                        value = tour_length(inst, trial)
                        if value < best[0] - 1e-10:
                            best = (value, trial)
                if best[1] is not None:
                    route = best[1]
                    improved = True
    return float(tour_length(inst, route)), tuple(route)


def route_of(inst: Instance, cluster, hint=None) -> tuple[float, tuple[int, ...]]:
    """Kürzeste Rundreise des Clusters: exakt bis EXACT_MAX Kunden, sonst die Heuristik ab `hint` (Voreinstellung: die Reihenfolge von `cluster`)."""
    if len(cluster) <= EXACT_MAX:
        return tsp_exact(inst, cluster)
    return tsp_heuristic(inst, cluster, hint)


def with_routing(inst: Instance, clusters) -> Plan:
    """Jedes Cluster als kürzeste Rundreise (Winkelfolge als Startfolge der Heuristik)."""
    routes, total = [], 0.0
    for cl in clusters:
        c, r = route_of(inst, cl, cl)
        total += c
        routes.append(r)
    return Plan(total, tuple(routes))


def in_order(inst: Instance, clusters) -> Plan:
    """Jedes Cluster in der Reihenfolge der Winkelfolge (kein zweiter Schritt)."""
    routes = tuple(tuple(c) for c in clusters)
    return Plan(A.plan_length(inst, routes), routes)


def reoptimize(inst: Instance, routes) -> Plan:
    """Jede Route eines fremden Plans (Savings, Einfügen nach Split) mit derselben Regel neu als kürzeste Rundreise (Startfolge: die vorhandene Route)."""
    return with_routing(inst, [list(r) for r in routes])


# ----------------------------------------------------------------------------------------------------------------------------------------- Sweep über alle Starts

def starts(inst: Instance, step: int = 1) -> list[tuple[int, int]]:
    """Alle Startpositionen (jede `step`-te) in beiden Richtungen: (k, Richtung), erst k, dann +1 vor -1."""
    return [(k, d) for k in range(0, inst.n, step) for d in (1, -1)]


def sweep_plan(inst: Instance, k: int = 0, direction: int = 1, routing: bool = True) -> Plan:
    clusters = sweep_clusters(inst, k, direction)
    return with_routing(inst, clusters) if routing else in_order(inst, clusters)


def all_starts(inst: Instance, routing: bool = True, step: int = 1) -> list[dict]:
    """Kosten und Routenzahl jedes Starts."""
    out = []
    for k, d in starts(inst, step):
        plan = sweep_plan(inst, k, d, routing)
        out.append({"k": k, "direction": d, "cost": plan.cost, "routes": len(plan.routes), "plan": plan})
    return out


def best_start(inst: Instance, routing: bool = True, step: int = 1) -> tuple[Plan, int, int]:
    """Der billigste Start (Gleichstand: der erste in der Reihenfolge von `starts`); Rückgabe: Plan, k, Richtung."""
    best = None
    for item in all_starts(inst, routing, step):
        if best is None or item["cost"] < best["cost"] - 1e-12:
            best = item
    return best["plan"], best["k"], best["direction"]


def split_best_start(inst: Instance, step: int = 1) -> A.SplitResult:
    """Die Winkelfolge als Riesentour mit optimalem Split (Stück 1), bester Start über alle Startpositionen und beide Richtungen."""
    base = angular_order(inst)
    best = None
    for k, d in starts(inst, step):
        r = A.split(inst, rotated(base, k, d))
        if best is None or r.cost < best.cost - 1e-12:
            best = r
    return best


# ----------------------------------------------------------------------------------------------------------------------------------------- Schnittoptimum

def cut_optimal(inst: Instance, step: int = 1) -> Plan:
    """Die beste Zerlegung der zyklischen Winkelfolge in zusammenhängende Cluster mit kürzester Rundreise je Cluster (jede `step`-te Startposition, beide Richtungen)."""
    base = angular_order(inst)
    n = inst.n
    cache: dict[tuple[int, ...], tuple[float, tuple[int, ...]]] = {}
    best: Plan | None = None
    for k, direction in starts(inst, step):
        order = rotated(base, k, direction)
        dp = [math.inf] * (n + 1)
        parent: list[int] = [-1] * (n + 1)
        dp[0] = 0.0
        for i in range(n):
            if dp[i] == math.inf:
                continue
            load = 0
            for j in range(i, n):
                load += inst.demand[order[j] - 1]
                if load > inst.capacity:
                    break
                seg = order[i:j + 1]
                key = tuple(sorted(seg))
                if key not in cache:
                    cache[key] = route_of(inst, list(seg), seg)
                if dp[i] + cache[key][0] < dp[j + 1] - 1e-12:
                    dp[j + 1] = dp[i] + cache[key][0]
                    parent[j + 1] = i
        if best is None or dp[n] < best.cost - 1e-12:
            routes, node = [], n
            while node > 0:
                i = parent[node]
                routes.append(cache[tuple(sorted(order[i:node]))][1])
                node = i
            best = Plan(dp[n], tuple(reversed(routes)))
    return best


# ----------------------------------------------------------------------------------------------------------------------------------------- Zählen

def n_sweep_partitions(n: int, k: int) -> int:
    """Zahl der Zerlegungen eines Kreises aus n Kunden in k zusammenhängende Gruppen: k Lücken von n (k >= 2), für k = 1 genau eine."""
    if not 1 <= k <= n:
        return 0
    return 1 if k == 1 else math.comb(n, k)


def stirling2(n: int, k: int) -> int:
    """Zahl aller Zerlegungen von n Kunden in k nichtleere Gruppen (Stirling-Zahl zweiter Art)."""
    if k == 0:
        return int(n == 0)
    if not 1 <= k <= n:
        return 0
    return sum((-1) ** (k - j) * math.comb(k, j) * j ** n for j in range(k + 1)) // math.factorial(k)


# ----------------------------------------------------------------------------------------------------------------------------------------- Prüfung: ist ein Plan eine Sweep-Zerlegung?

def route_blocks(inst: Instance, route) -> int:
    """Zahl der zusammenhängenden Stücke, aus denen die Kunden der Route in der zyklischen Winkelfolge bestehen (eine Route aus allen Kunden: 0)."""
    base = angular_order(inst)
    pos = {c: i for i, c in enumerate(base)}
    idx = {pos[c] for c in route}
    n = len(base)
    return sum(1 for p in idx if (p + 1) % n not in idx)


def is_sweep_partition(inst: Instance, routes) -> bool:
    """Besteht jede Route aus aufeinanderfolgenden Kunden der zyklischen Winkelfolge?"""
    return all(route_blocks(inst, r) <= 1 for r in routes)


def route_arcs(inst: Instance, routes) -> list[dict]:
    """Je Route: Winkelbereich in Grad (von dem ersten bis zum letzten Kunden der Winkelfolge) und ob die Route ein zusammenhängendes Stück ist."""
    base = angular_order(inst)
    pos = {c: i for i, c in enumerate(base)}
    out = []
    for r in routes:
        blocks = route_blocks(inst, r)
        idx = sorted(pos[c] for c in r)
        if blocks <= 1 and len(idx) < len(base):
            n = len(base)
            start = next(p for p in idx if (p - 1) % n not in idx)
            end = (start + len(idx) - 1) % n
            out.append({"route": tuple(r), "contiguous": True, "from_deg": math.degrees(angle_of(inst, base[start])), "to_deg": math.degrees(angle_of(inst, base[end]))})
        else:
            out.append({"route": tuple(r), "contiguous": blocks <= 1, "from_deg": None, "to_deg": None})
    return out
