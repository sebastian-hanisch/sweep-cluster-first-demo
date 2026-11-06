"""Erzeuger der Reihenfolgen für den Vergleich (aus riesentouren-erzeugen-demo und split-gegen-fuellen-demo kopiert und umbenannt, ohne `larger_place`).

Gleichstände: bei Kunden die kleinere Nummer, bei Stellen die kleinere Stelle. Eine Stelle p heißt: vor den p-ten Kunden der Folge."""

import swp_algorithm as A
import swp_constants as C
from swp_scenario import Instance, distance_matrix


def farthest_insertion_order(inst: Instance) -> tuple[int, ...]:
    """Fernstes Einfügen: Start mit dem Kunden am weitesten vom Depot, dann der Kunde am weitesten von der bisherigen Rundreise an der Stelle mit der kleinsten Längenzunahme."""
    D = distance_matrix(inst)
    far = max(range(1, inst.n + 1), key=lambda c: (D[0][c], -c))
    tour = [0, far]
    left = set(range(1, inst.n + 1)) - {far}
    while left:
        pick = max(sorted(left), key=lambda c: (min(D[c][t] for t in tour), -c))
        best = None
        for k in range(len(tour)):
            a, b = tour[k], tour[(k + 1) % len(tour)]
            added = D[a][pick] + D[pick][b] - D[a][b]
            if best is None or added < best[0] - C.TIE:
                best = (added, k + 1)
        tour.insert(best[1], pick)
        left.remove(pick)
    return tuple(tour[1:])


def insert_split_order(inst: Instance) -> tuple[int, ...]:
    """Einfügen nach Split: Kunden in absteigender Entfernung vom Depot, jeder an der Stelle mit den kleinsten Split-Kosten der Teilfolge."""
    D = distance_matrix(inst)
    sequence = sorted(range(1, inst.n + 1), key=lambda c: (-D[0][c], c))
    order: tuple[int, ...] = ()
    for c in sequence:
        best = None
        for p in range(len(order) + 1):
            trial = order[:p] + (c,) + order[p:]
            cost = A.split(inst, trial).cost
            if best is None or cost < best[0] - C.TIE:
                best = (cost, trial)
        order = best[1]
    return order
