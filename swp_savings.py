"""Savings (Clarke und Wright, 1964) mit Formparametern, sequentielle Fassung und verrauschte Mehrfachläufe (aus savings-gegen-split-demo, Stück 4 der Linie, kopiert, umbenannt und erweitert).

Ersparnis eines Paares (i, j):
    s(i, j) = d(0,i) + d(0,j) - lam * d(i,j) + mu * |d(0,i) - d(0,j)| + nu * (q_i + q_j) / q_mittel
lam = 1, mu = nu = 0 ist die klassische Ersparnis aus Stück 4. lam stammt laut Sekundärquellen von Gaskell (1967) und Yellow (1970), mu und nu von Paessens (1988); die Formel ist nach Sekundärquellen
übernommen und nicht an der Originalarbeit geprüft. q_mittel ist die mittlere Nachfrage aller Kunden.

Parallele Fassung: Jeder Kunde fährt zuerst allein. Die Paare mit s > 0 werden in absteigender Ersparnis abgearbeitet; ein Paar legt zwei Routen zusammen, wenn i und j in verschiedenen Routen stehen,
beide am Rand ihrer Route (erster oder letzter Kunde) und die Last in ein Fahrzeug passt; Routen dürfen dabei umgedreht werden. Gleichstände: größere Ersparnis, dann kleineres i, dann kleineres j.
Die Routen eines Plans stehen in der Reihenfolge ihrer Kennungen (Kennung: die Nummer des linken Kunden i des Paares, dessen Route erhalten bleibt).

Sequentielle Fassung: eine Route nach der anderen. Start beim am weitesten vom Depot entfernten freien Kunden (Gleichstand: kleinere Nummer), dann wird am Anfang oder Ende der Route der Kunde mit der größten
Ersparnis zum jeweiligen Randkunden angefügt, solange die Last passt und die Ersparnis positiv ist; danach beginnt die nächste Route.

Rauschen: jede Ersparnis wird mit (1 + eps * U[-1, 1]) multipliziert (U gleichverteilt, je Paar unabhängig). Das ist ein eigener, einfacher Ansatz und nicht die verzerrte Zufallsauswahl von Juan u. a. (2011)."""

from dataclasses import dataclass

import numpy as np

import swp_algorithm as A
from swp_scenario import Instance, distance_matrix

# Ausgänge eines Paares
MERGED, SAME_ROUTE, NO_END, CAPACITY = "merged", "same", "no_end", "capacity"
OUTCOME_TEXT = {MERGED: "legt zusammen", SAME_ROUTE: "schon dieselbe Route", NO_END: "kein Randkunde", CAPACITY: "blockiert durch die Kapazität"}
NOISE_SEED_OFFSET = 11                       # Rauschläufe einer Instanz mit Seed s ziehen aus numpy.random.default_rng(s + 11)


@dataclass(frozen=True)
class Params:
    lam: float = 1.0
    mu: float = 0.0
    nu: float = 0.0


STANDARD = Params()


@dataclass(frozen=True)
class Step:
    rank: int                     # Platz in der Liste der Paare mit s > 0 (ab 1)
    i: int
    j: int
    saving: float
    outcome: str
    routes: tuple[tuple[int, ...], ...]   # alle Routen NACH diesem Schritt


@dataclass(frozen=True)
class SavingsResult:
    routes: tuple[tuple[int, ...], ...]
    steps: tuple[Step, ...]

    @property
    def merges(self) -> int:
        return sum(s.outcome == MERGED for s in self.steps)

    def count(self, outcome: str) -> int:
        return sum(s.outcome == outcome for s in self.steps)


# ----------------------------------------------------------------------------------------------------------------------------------------- Ersparnisse

def pair_arrays(inst: Instance, params: Params = STANDARD):
    """Alle Paare i < j (Kundennummern ab 1) als Arrays (i, j, s) in der Reihenfolge von numpy.triu_indices; s kann auch negativ sein."""
    D = distance_matrix(inst)
    q = np.array(inst.demand, dtype=float)
    iu, ju = np.triu_indices(inst.n, 1)
    d0 = D[0][1:]
    s = d0[iu] + d0[ju] - params.lam * D[iu + 1, ju + 1] + params.mu * np.abs(d0[iu] - d0[ju]) + params.nu * (q[iu] + q[ju]) / q.mean()
    return iu + 1, ju + 1, s


def _sorted_pairs(i, j, s):
    order = np.lexsort((j, i, -s))
    return [(float(s[k]), int(i[k]), int(j[k])) for k in order if s[k] > 0]


def savings_list(inst: Instance, params: Params = STANDARD) -> list[tuple[float, int, int]]:
    """Alle Paare i < j mit s(i, j) > 0, absteigend nach Ersparnis, Gleichstand: kleinere Nummern zuerst."""
    return _sorted_pairs(*pair_arrays(inst, params))


def noisy_list(inst: Instance, params: Params, eps: float, rng) -> list[tuple[float, int, int]]:
    """Die Liste mit verrauschten Ersparnissen (alle Paare ziehen eine Zufallszahl, auch die mit s <= 0; dann zählen nur die mit verrauschtem s > 0)."""
    i, j, s = pair_arrays(inst, params)
    if eps > 0:
        s = s * (1 + eps * rng.uniform(-1, 1, size=s.shape))
    return _sorted_pairs(i, j, s)


# ----------------------------------------------------------------------------------------------------------------------------------------- parallel

def _merge(inst: Instance, routes, where, load, i: int, j: int) -> str:
    """Ein Paar abarbeiten (verändert routes, where und load); Rückgabe: der Ausgang."""
    ri, rj = where[i], where[j]
    if ri == rj:
        return SAME_ROUTE
    a, b = routes[ri], routes[rj]
    if not ((a[0] == i or a[-1] == i) and (b[0] == j or b[-1] == j)):
        return NO_END
    if load[ri] + load[rj] > inst.capacity:
        return CAPACITY
    if a[-1] == i and b[0] == j:
        new = a + b
    elif a[0] == i and b[-1] == j:
        new = b + a
    elif a[0] == i and b[0] == j:
        new = a[::-1] + b
    else:
        new = a + b[::-1]
    routes[ri] = new
    load[ri] += load[rj]
    del routes[rj], load[rj]
    for c in new:
        where[c] = ri
    return MERGED


def _start(inst: Instance):
    routes = {i: [i] for i in range(1, inst.n + 1)}
    return routes, {i: i for i in routes}, {i: inst.demand[i - 1] for i in routes}


def run_pairs(inst: Instance, pairs) -> tuple[tuple[int, ...], ...]:
    """Die Paare in dieser Reihenfolge abarbeiten (ohne Spur); Ergebnis: die Routen."""
    routes, where, load = _start(inst)
    for _, i, j in pairs:
        _merge(inst, routes, where, load, i, j)
    return tuple(tuple(r) for r in routes.values())


def savings_routes(inst: Instance, params: Params = STANDARD, pairs=None) -> tuple[tuple[int, ...], ...]:
    """Dieselben Routen wie `savings(...).routes`, ohne Spur (schneller, für Mehrfachläufe)."""
    return run_pairs(inst, pairs if pairs is not None else savings_list(inst, params))


def savings(inst: Instance, params: Params = STANDARD, pairs=None) -> SavingsResult:
    """Parallele Savings mit Spur (eine Zeile je Paar mit s > 0). `pairs`: eine fertige Liste (z. B. verrauscht) statt der Liste zu `params`."""
    routes, where, load = _start(inst)
    steps = []
    for rank, (s, i, j) in enumerate(pairs if pairs is not None else savings_list(inst, params), start=1):
        outcome = _merge(inst, routes, where, load, i, j)
        steps.append(Step(rank, i, j, s, outcome, tuple(tuple(r) for r in routes.values())))
    return SavingsResult(tuple(tuple(r) for r in routes.values()), tuple(steps))


def routes_after(inst: Instance, result: SavingsResult, step: int) -> tuple[tuple[int, ...], ...]:
    """Die Routen nach den ersten `step` Paaren (0: jeder Kunde allein)."""
    if step <= 0:
        return tuple((c,) for c in range(1, inst.n + 1))
    return result.steps[min(step, len(result.steps)) - 1].routes


def savings_then_split(inst: Instance, routes) -> A.SplitResult:
    """Die Routen hintereinander als Riesentour, danach der optimale Split (nie schlechter als die Routen selbst)."""
    return A.split(inst, A.concatenate(routes))


# ----------------------------------------------------------------------------------------------------------------------------------------- sequentiell

def savings_sequential(inst: Instance, params: Params = STANDARD) -> tuple[tuple[int, ...], ...]:
    """Sequentielle Fassung: eine Route nach der anderen (siehe Modulkopf)."""
    D = distance_matrix(inst)
    q = inst.demand
    qbar = sum(q) / len(q)

    def value(i: int, j: int) -> float:
        return float(D[0][i] + D[0][j] - params.lam * D[i][j] + params.mu * abs(D[0][i] - D[0][j]) + params.nu * (q[i - 1] + q[j - 1]) / qbar)

    left = set(range(1, inst.n + 1))
    routes = []
    while left:
        start = max(sorted(left), key=lambda c: (D[0][c], -c))
        route, load = [start], q[start - 1]
        left.remove(start)
        while True:
            best = None
            for c in sorted(left):
                if load + q[c - 1] > inst.capacity:
                    continue
                for side, end in ((0, route[0]), (1, route[-1])):
                    v = value(end, c)
                    if best is None or v > best[0] + 1e-12:
                        best = (v, c, side)
            if best is None or best[0] <= 0:
                break
            _, c, side = best
            route = [c] + route if side == 0 else route + [c]
            load += q[c - 1]
            left.remove(c)
        routes.append(tuple(route))
    return tuple(routes)


# ----------------------------------------------------------------------------------------------------------------------------------------- Mehrfachläufe

def canonical(routes) -> tuple[tuple[int, ...], ...]:
    """Pläne gleich bis auf Richtung und Reihenfolge der Routen."""
    return tuple(sorted(tuple(r) if r[0] <= r[-1] else tuple(r[::-1]) for r in routes))


def noise_runs(inst: Instance, params: Params, eps: float, k: int, seed: int) -> list[tuple[tuple[int, ...], ...]]:
    """k verrauschte Läufe (die Zufallszahlen kommen nacheinander aus einem Erzeuger mit Seed seed + 11)."""
    rng = np.random.default_rng(seed + NOISE_SEED_OFFSET)
    return [savings_routes(inst, params, pairs=noisy_list(inst, params, eps, rng)) for _ in range(k)]


def swap_sensitivity(inst: Instance, params: Params = STANDARD) -> list[dict]:
    """Kippstellen: Je zwei benachbarte Paare der Liste (Platz r und r + 1) werden vertauscht; geändert wird nur, wenn sich der Plan ändert.
    Rückgabe: je Vertauschung r, die Paare, ob sich der Plan ändert, und die Kostenänderung in Prozent (neu minus alt, bezogen auf alt)."""
    pairs = savings_list(inst, params)
    base = run_pairs(inst, pairs)
    base_cost = A.plan_length(inst, base)
    out = []
    for r in range(len(pairs) - 1):
        swapped = pairs[:r] + [pairs[r + 1], pairs[r]] + pairs[r + 2:]
        alt = run_pairs(inst, swapped)
        changed = canonical(alt) != canonical(base)
        change = 100.0 * (A.plan_length(inst, alt) - base_cost) / base_cost if changed and base_cost > 0 else 0.0
        out.append({"rank": r + 1, "first": pairs[r], "second": pairs[r + 1], "changed": changed, "change_pct": change})
    return out


LAMS = tuple(round(0.4 + 0.2 * k, 1) for k in range(9))          # die neun λ-Werte der Mehrfachrechnung: 0,4 bis 2,0
GRID = tuple((lam, mu, nu) for lam in (0.8, 1.0, 1.2, 1.4) for mu in (0.0, 0.5, 1.0) for nu in (0.0, 0.5, 1.0))   # 36 Tripel
NOISE_EPS = 0.01                                                    # Rauschen der Mehrfachrechnung (1 %)
NOISE_RUNS = 20


def best_of(inst: Instance, plans) -> tuple[float, tuple[tuple[int, ...], ...]]:
    """Der billigste Plan; bei Gleichstand der erste."""
    best = None
    for routes in plans:
        cost = A.plan_length(inst, routes)
        if best is None or cost < best[0] - 1e-12:
            best = (cost, routes)
    return best
