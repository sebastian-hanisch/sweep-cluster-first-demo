"""Kennzahlen, Verdikt-Logik und Bänder. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

import swp_algorithm as A
import swp_constants as C
import swp_construct as K
import swp_savings as S
import swp_sweep as W
from swp_scenario import Instance, make_instance
from swp_sweep import Plan


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    depot: int = C.DEFAULT_DEPOT
    routes: int = C.DEFAULT_ROUTES
    fill: int = C.DEFAULT_FILL
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True, eq=False)
class Analysis:
    settings: Settings
    inst: Instance
    exact: A.ExactResult                 # Optimum über alle Tourenpläne
    min_routes: int                      # aufgerundet Gesamtnachfrage / Kapazität
    plans: dict                          # Strategie-Schlüssel -> Plan
    starts: list                         # je Startposition und Richtung: k, direction, cost (mit Rundreise), routes (Zahl), cost_order (Winkelfolge)
    opt_sweep: bool                      # ist das Optimum eine Zerlegung der zyklischen Winkelfolge in zusammenhängende Stücke?
    opt_arcs: list                       # Winkelbereich je Route des Optimums


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def signed_pct(x: float, digits: int = 1) -> str:
    """Mit Vorzeichen (echtes Minus); -0,0 wird zu 0,0."""
    text = de(abs(x), digits)
    if float(text.replace(",", ".")) == 0.0:
        return f"{text} %"
    return f"{'+' if x > 0 else '−'}{text} %"


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def instances_word(k: int) -> str:
    return f"{k} Instanz" if k == 1 else f"{k} Instanzen"


def gap_percent(cost: float, reference: float) -> float:
    """Mehrkosten gegenüber der Referenz in Prozent der Referenz; unter der Toleranz oder ohne Referenzkosten gibt es keinen Abstand, nie negativ."""
    if reference <= 0 or cost - reference <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


def diff_percent(a: float, b: float) -> float:
    """Unterschied (a - b) in Prozent von b; innerhalb der Toleranz 0."""
    if abs(a - b) <= C.TOL or b <= 0:
        return 0.0
    return 100.0 * (a - b) / b


def order_text(order) -> str:
    return " ".join(str(c) for c in order)


def routes_text(routes) -> str:
    return " ‖ ".join("(" + order_text(r) + ")" for r in routes)


def direction_text(direction: int) -> str:
    return "gegen den Uhrzeigersinn" if direction > 0 else "mit dem Uhrzeigersinn"


# ----------------------------------------------------------------------------------------------------------------------------------- Analyse

def build_instance(settings: Settings) -> Instance:
    return make_instance(settings.n, settings.family, settings.depot, settings.routes, settings.seed, settings.fill)


def savings_plans(inst: Instance) -> tuple[Plan, Plan, Plan]:
    """Savings mit λ = 1 (so wie es ist), dasselbe mit Rundreise je Route, und das Beste von 9 λ-Werten jeweils mit Rundreise je Route."""
    sp1 = S.savings_routes(inst)
    sp1_plain = Plan(A.plan_length(inst, sp1), tuple(sp1))
    sp1_r = W.reoptimize(inst, sp1)
    best = None
    for lam in S.LAMS:
        r = W.reoptimize(inst, S.savings_routes(inst, S.Params(lam)))
        if best is None or r.cost < best.cost - 1e-12:
            best = r
    return sp1_plain, sp1_r, best


def insertion_plans(inst: Instance) -> tuple[Plan, Plan]:
    es = A.split(inst, K.insert_split_order(inst))
    es_plain = Plan(es.cost, es.routes)
    return es_plain, W.reoptimize(inst, es.routes)


def analyse(settings: Settings) -> Analysis:
    inst = build_instance(settings)
    exact = A.exact_cvrp(inst)
    plans = {"sw0_order": W.sweep_plan(inst, 0, 1, False), "sw0": W.sweep_plan(inst, 0, 1, True)}
    plans["swb_order"] = W.best_start(inst, False)[0]
    plans["swb"] = W.best_start(inst, True)[0]
    split = W.split_best_start(inst)
    plans["splitb"] = Plan(split.cost, split.routes)
    plans["cut"] = W.cut_optimal(inst)
    plans["sp1"], plans["sp1_r"], plans["lam9_r"] = savings_plans(inst)
    plans["es"], plans["es_r"] = insertion_plans(inst)
    starts = []
    for k, d in W.starts(inst):
        r = W.sweep_plan(inst, k, d, True)
        o = W.sweep_plan(inst, k, d, False)
        starts.append({"k": k, "direction": d, "cost": r.cost, "routes": len(r.routes), "cost_order": o.cost, "clusters": len(W.sweep_clusters(inst, k, d))})
    return Analysis(settings, inst, exact, inst.min_routes, plans, starts, W.is_sweep_partition(inst, exact.routes), W.route_arcs(inst, exact.routes))


def sweep_view(settings: Settings, k: int, direction: int, routing: bool) -> dict:
    """Experiment 1: der Sweep ab Position k in der gewählten Richtung."""
    inst = build_instance(settings)
    base = W.angular_order(inst)
    order = W.rotated(base, k, direction)
    clusters = W.fill_until_full(inst, order)
    plan = W.with_routing(inst, clusters) if routing else W.in_order(inst, clusters)
    D = inst
    cluster_of = {c: i + 1 for i, cl in enumerate(clusters) for c in cl}
    table = [{"customer": c, "angle": math.degrees(W.angle_of(inst, c)), "distance": math.dist(D.xy[0], D.xy[c]), "demand": inst.demand[c - 1], "cluster": cluster_of[c]} for c in order]
    return {"order": order, "clusters": clusters, "plan": plan, "table": table, "loads": [inst.load(cl) for cl in clusters]}


def boundary_angles(inst: Instance, order, clusters) -> list[float]:
    """Winkel (Bogenmaß) der Schnitte zwischen den Clustern: Mitte zwischen dem letzten Kunden eines Clusters und dem ersten des nächsten (auf dem Kreis gemessen)."""
    out = []
    flat = [c for cl in clusters for c in cl]
    pos = 0
    for cl in clusters[:-1]:
        pos += len(cl)
        a, b = W.angle_of(inst, flat[pos - 1]), W.angle_of(inst, flat[pos])
        delta = (b - a) % (2 * math.pi)
        out.append((a + delta / 2) % (2 * math.pi))
    return out


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def _reopt_cost(inst: Instance, routes) -> float:
    return W.reoptimize(inst, routes).cost


def instance_row(n: int, family: int, depot: int, routes: int, seed: int, fill: int, ref: float, es: float, sp1: float, lam9: float) -> dict:
    """Eine feste Instanz der Bänder: Referenz und Kosten von Einfügen nach Split, Savings (λ = 1 und bestes von 9) aus Stück 5 übernommen, alles andere frisch."""
    inst = make_instance(n, family, depot, routes, seed, fill)
    step = C.BAND_START_STEP.get(n, 1)
    base = W.angular_order(inst)
    row = {"seed": seed, "m": inst.min_routes, "ref": ref, "es": es, "sp1": sp1, "lam9": lam9}
    clusters0 = W.sweep_clusters(inst, 0, 1)
    row["sw0_k"] = len(clusters0)
    row["sw0_order"] = W.in_order(inst, clusters0).cost
    row["sw0"] = W.with_routing(inst, clusters0).cost
    variants = W.starts(inst, step)
    best_order = best_route = math.inf
    over = 0
    for k, d in variants:
        clusters = W.fill_until_full(inst, W.rotated(base, k, d))
        best_order = min(best_order, W.in_order(inst, clusters).cost)
        best_route = min(best_route, W.with_routing(inst, clusters).cost)
        over += len(clusters) > inst.min_routes
    row["swb_order"], row["swb"], row["swb_over_m"] = best_order, best_route, over / len(variants)
    row["splitb"] = W.split_best_start(inst, step).cost
    if n <= C.CUT_MAX_N:
        row["cut"] = W.cut_optimal(inst, step).cost
    row["sp1_r"] = W.reoptimize(inst, S.savings_routes(inst)).cost
    row["lam9_r"] = min(_reopt_cost(inst, S.savings_routes(inst, S.Params(lam))) for lam in S.LAMS)
    if n <= C.ES_R_MAX_N:
        row["es_r"] = _reopt_cost(inst, A.split(inst, K.insert_split_order(inst)).routes)
    if n <= C.N_MAX:
        ex = A.exact_cvrp(inst)
        row["opt_is_sweep"] = W.is_sweep_partition(inst, ex.routes)
        row["k_opt"] = len(ex.routes)
    return row


@lru_cache(maxsize=1)
def load_bands() -> dict:
    """Vorberechnete Bänder (generate_precomputed.py); {} wenn die Datei fehlt."""
    path = Path(__file__).with_name(C.BAND_FILE)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def band_rows(n: int, fill: int, routes: int = C.BAND_ROUTES) -> list[dict]:
    """Alle gespeicherten Instanzzeilen einer Größe, Auslastung und Zielroutenzahl, Zellen in der Reihenfolge von BAND_CELLS; jede Zeile trägt `family` und `depot` ihrer Zelle."""
    order = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
    cells = sorted((c for c in load_bands().get("cells", []) if c["n"] == n and c["fill"] == fill and c["routes"] == routes), key=lambda c: order[(c["family"], c["depot"])])
    return [{**r, "family": c["family"], "depot": c["depot"]} for c in cells for r in c["rows"]]


def spread(values: list[float]) -> dict:
    return {"min": min(values), "median": median(values), "mean": mean(values), "max": max(values), "hit": sum(v == 0.0 for v in values), "count": len(values)}


def paired(a: list[float], b: list[float]) -> dict:
    """Gepaarter Vergleich: a billiger / gleich / teurer als b, dazu der Median des Unterschieds in Prozent von b."""
    cheaper = sum(x < y - C.TOL for x, y in zip(a, b))
    more = sum(x > y + C.TOL for x, y in zip(a, b))
    return {"count": len(a), "cheaper": cheaper, "equal": len(a) - cheaper - more, "more": more, "median_diff": median(diff_percent(x, y) for x, y in zip(a, b)) if a else 0.0}


def band_stats(rows: list[dict]) -> dict:
    """Alle Kennzahlen einer Größe, Auslastung und Zielroutenzahl aus den gespeicherten Zeilen."""
    if not rows:
        return {}
    keys = [k for k in C.STRATEGY_KEYS if all(k in r for r in rows)]
    gaps = {k: spread([gap_percent(r[k], r["ref"]) for r in rows]) for k in keys}
    vs = {k: paired([r[k] for r in rows], [r[C.COMPARE_KEY] for r in rows]) for k in keys if k != C.COMPARE_KEY}
    by_depot = {d: {k: median(gap_percent(r[k], r["ref"]) for r in rows if r["depot"] == d) for k in ("sw0", "swb", "sp1_r", "cut") if k in keys and any(r["depot"] == d for r in rows)} for d in (0, 1)}
    by_family = {f: {k: median(gap_percent(r[k], r["ref"]) for r in rows if r["family"] == f) for k in ("swb", "sp1_r") if any(r["family"] == f for r in rows)} for f in (1, 2)}
    out = {
        "count": len(rows), "keys": keys, "gaps": gaps, "vs": vs, "by_depot": by_depot, "by_family": by_family,
        "over_m": sum(r["sw0_k"] > r["m"] for r in rows), "over_m_share": mean(r["swb_over_m"] for r in rows),
    }
    if all("opt_is_sweep" in r for r in rows):
        out["opt_is_sweep"] = sum(r["opt_is_sweep"] for r in rows)
        out["opt_over_m"] = sum(r["k_opt"] > r["m"] for r in rows)
    if "cut" in keys:
        out["cluster_loss"] = spread([gap_percent(r["cut"], r["ref"]) for r in rows])
        out["routing_loss"] = median(100 * (r["sw0_order"] - r["sw0"]) / r["sw0"] for r in rows)
        out["cut_loss"] = median(100 * (r["sw0"] - r["cut"]) / r["cut"] for r in rows)
    return out


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_sweep(a: Analysis, k: int, direction: int, routing: bool, view: dict) -> tuple[str, str]:
    """Experiment 1: der gewählte Sweep."""
    plan, clusters = view["plan"], view["clusters"]
    gap = gap_percent(plan.cost, a.exact.cost)
    how = "kürzeste Rundreise je Cluster" if routing else "Winkelfolge je Cluster"
    text = (f"Sweep ab Position {k + 1} der Winkelfolge, {direction_text(direction)}, {how}: {routes_word(len(clusters))} mit den Lasten {', '.join(str(x) for x in view['loads'])} (Kapazität {a.inst.capacity}). "
            f"Länge {de(plan.cost)}, {pct(gap)} über dem Optimum {de(a.exact.cost)}. ")
    if len(clusters) > a.min_routes:
        text += f"Der Sweep braucht {routes_word(len(clusters))}; die Mindestroutenzahl ist {a.min_routes} (mit dieser Flottengrenze wäre er nicht zulässig). "
    kind = "success" if plan.cost <= a.exact.cost + C.TOL else ("warning" if gap >= C.GAP_WARN else "info")
    return kind, text.rstrip()


def verdict_starts(a: Analysis) -> tuple[str, str]:
    """Experiment 2: alle Startpositionen und beide Richtungen."""
    rows = a.starts
    costs = [r["cost"] for r in rows]
    best, worst = min(rows, key=lambda r: (r["cost"], r["k"], -r["direction"])), max(rows, key=lambda r: r["cost"])
    fixed = rows[0]
    over = sum(r["clusters"] > a.min_routes for r in rows)
    text = (f"Von {len(rows)} Starts (Position und Richtung) kostet der feste Start {de(fixed['cost'])} ({pct(gap_percent(fixed['cost'], a.exact.cost))} über dem Optimum {de(a.exact.cost)}), "
            f"der beste (Position {best['k'] + 1}, {direction_text(best['direction'])}) {de(best['cost'])} ({pct(gap_percent(best['cost'], a.exact.cost))}), der schlechteste {de(worst['cost'])} "
            f"({pct(gap_percent(worst['cost'], a.exact.cost))}); {len({round(c, 6) for c in costs})} verschiedene Kosten. ")
    text += f"{over} der {len(rows)} Starts brauchen mehr als die Mindestroutenzahl {a.min_routes} Routen." if over else f"Kein Start braucht mehr als die Mindestroutenzahl {a.min_routes} Routen."
    return ("success" if best["cost"] <= a.exact.cost + C.TOL else "info"), text


def verdict_losses(a: Analysis) -> tuple[str, str]:
    """Experiment 3: Zerlegung der Verluste auf der Instanz."""
    p, opt = a.plans, a.exact.cost
    text = (f"Das Optimum ist {de(opt)}. Die beste Zerlegung der Winkelfolge in zusammenhängende Cluster mit Rundreise je Cluster (Schnittoptimum) kostet {de(p['cut'].cost)} ({pct(gap_percent(p['cut'].cost, opt))} darüber): "
            f"das ist der Verlust, den schon die Gruppenbildung nach dem Winkel kostet. Der feste Start mit „Füllen bis voll“ kostet {de(p['sw0'].cost)} ({pct(gap_percent(p['sw0'].cost, opt))}): "
            f"der Schnitt-Verlust gegen das Schnittoptimum ist {pct(diff_percent(p['sw0'].cost, p['cut'].cost))}. Mit der Winkelfolge statt der Rundreise je Cluster kostet er {de(p['sw0_order'].cost)} "
            f"({pct(gap_percent(p['sw0_order'].cost, opt))}). ")
    text += ("Das Optimum besteht aus zusammenhängenden Stücken der Winkelfolge: Eine Sweep-Zerlegung kann es erreichen." if a.opt_sweep
             else "Das Optimum ist keine Sweep-Zerlegung: Mindestens eine seiner Routen nimmt Kunden aus getrennten Stücken der Winkelfolge, kein Sweep kann es erreichen.")
    return ("success" if p["cut"].cost <= opt + C.TOL else ("warning" if gap_percent(p["cut"].cost, opt) >= C.GAP_WARN else "info")), text


def verdict_compare(a: Analysis) -> tuple[str, str]:
    """Experiment 4 und Kernfrage: Sweep gegen Savings und Einfügen nach Split mit gleicher Rundreise je Route."""
    p, opt = a.plans, a.exact.cost
    sw, sv, es = p["swb"].cost, p["sp1_r"].cost, p["es_r"].cost
    d = diff_percent(sw, sv)
    text = (f"Mit der gleichen Rundreise je Route kostet der Sweep (bester Start) {de(sw)} ({pct(gap_percent(sw, opt))} über dem Optimum {de(opt)}), Savings (λ = 1) {de(sv)} ({pct(gap_percent(sv, opt))}), "
            f"Einfügen nach Split {de(es)} ({pct(gap_percent(es, opt))}). ")
    if d == 0.0:
        text += "Sweep und Savings kosten dasselbe."
    elif d < 0:
        text += f"Der Sweep ist {pct(-d)} billiger als Savings."
    else:
        text += f"Der Sweep ist {pct(d)} teurer als Savings."
    best_other = min(p["sp1_r"].cost, p["lam9_r"].cost, p["es_r"].cost)
    kind = "success" if sw <= opt + C.TOL else ("warning" if gap_percent(sw, opt) >= C.GAP_WARN else "info")
    if sw < best_other - C.TOL:
        text += " Er ist hier das billigste der drei Verfahren."
    return kind, text


def _gap_part(name: str, s: dict) -> str:
    return f"{name} Median {pct(s['median'])} (Maximum {pct(s['max'])})"


def verdict_bands(n: int, fill: int, routes: int, stats: dict) -> tuple[str, str]:
    """Experiment 5: Bänder einer Größe, Auslastung und Zielroutenzahl (alle vier Zellen zusammen)."""
    if not stats:
        return "warning", f"Die vorberechneten Bänder fehlen ({C.BAND_FILE})."
    vs = stats["vs"]["swb"]
    d = vs["median_diff"]
    g = stats["gaps"]
    if abs(d) < C.LEVEL_PP:
        lead = f"Der Sweep (bester Start + Rundreise) und Savings (λ = 1 + Rundreise) liegen im Median gleichauf (Unterschied {signed_pct(d)}"
    elif d < 0:
        lead = f"Der Sweep (bester Start + Rundreise) liegt im Median vor Savings (λ = 1 + Rundreise) (Unterschied {signed_pct(d)}"
    else:
        lead = f"Savings (λ = 1 + Rundreise) liegt im Median vor dem Sweep (bester Start + Rundreise) (Unterschied {signed_pct(d)}"
    lead += f"; Sweep billiger / gleich / teurer: {vs['cheaper']} / {vs['equal']} / {vs['more']} von {vs['count']}). "
    ref = "zum exakten Optimum" if n in C.EXACT_SIZES else "zur Referenz PyVRP (keine bewiesene Untergrenze)"
    lead += f"Abstand {ref}: {_gap_part('Sweep, bester Start + Rundreise', g['swb'])}, {_gap_part('Sweep, fester Start + Rundreise', g['sw0'])}, {_gap_part('Savings + Rundreise', g['sp1_r'])}."
    kind = "info" if g["swb"]["median"] < C.GAP_WARN else "warning"
    return kind, f"Bei n = {n}, {routes_word(routes)}, Auslastung {fill} % ({instances_word(stats['count'])}): " + lead


def verdict_fleet(stats: dict) -> tuple[str, str]:
    """Experiment 5: wie oft der Sweep mehr als die Mindestroutenzahl braucht."""
    if not stats:
        return "warning", f"Die vorberechneten Bänder fehlen ({C.BAND_FILE})."
    text = (f"Der Sweep mit festem Start braucht mehr als die Mindestroutenzahl m Routen in {stats['over_m']} von {stats['count']} Instanzen; über alle Startpositionen im Mittel in {de(100 * stats['over_m_share'], 0)} % der Starts")
    if "opt_over_m" in stats:
        text += f". Das Optimum fährt in {stats['opt_over_m']} Instanzen mehr als m Routen"
    return ("warning" if stats["over_m"] > stats["count"] / 2 else "info"), text + "."


def verdict_optimum_sweep(stats: dict) -> tuple[str, str]:
    """Experiment 5: wie oft das Optimum eine Sweep-Zerlegung ist (nur exakte Größen)."""
    if not stats or "opt_is_sweep" not in stats:
        return "info", "Für diese Größe liegt kein exaktes Optimum vor: Ob das Optimum eine Sweep-Zerlegung ist, lässt sich nicht prüfen."
    k = stats["opt_is_sweep"]
    return "info", f"Das exakte Optimum besteht aus zusammenhängenden Stücken der Winkelfolge (ist eine Sweep-Zerlegung) in {k} von {stats['count']} Instanzen."


def verdict_depot(stats: dict) -> tuple[str, str]:
    """Experiment 5: Depot in der Mitte gegen Depot in der Ecke."""
    if not stats:
        return "warning", f"Die vorberechneten Bänder fehlen ({C.BAND_FILE})."
    mid, corner = stats["by_depot"][0], stats["by_depot"][1]
    worse = corner["swb"] > mid["swb"] + C.TOL
    text = (f"Sweep (bester Start + Rundreise), Median des Abstands: Depot in der Mitte {pct(mid['swb'])}, in der Ecke {pct(corner['swb'])}; Savings + Rundreise: {pct(mid['sp1_r'])} und {pct(corner['sp1_r'])}. "
            + ("Für den Sweep ist die Ecke hier schlechter." if worse else "Für den Sweep ist die Ecke hier nicht schlechter."))
    return "info", text
