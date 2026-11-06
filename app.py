"""Sweep und Cluster-first - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 6 der Reihe „Tourenbildung“: Erst Gruppen bilden, dann je Gruppe die Reihenfolge (cluster-first, route-second), am Beispiel des Sweeps: Kunden nach dem Winkel um das Depot ordnen und in dieser Folge
Routen füllen. Die Demo zeigt den Sweep Schritt für Schritt, was Start, Rundreise je Cluster, Kapazität und Depotlage ausmachen und wie er sich gegen Savings und Einfügen nach Split schlägt, live bis 12 Kunden
gegen das exakte Optimum und in vorberechneten Bändern bis 100 Kunden.

Lauffähig mit: streamlit run app.py
"""

import math

import streamlit as st

import swp_constants as C
import swp_sweep as W
from swp_evaluation import (
    Settings,
    analyse,
    band_rows,
    band_stats,
    boundary_angles,
    build_instance,
    de,
    diff_percent,
    gap_percent,
    instances_word,
    order_text,
    pct,
    routes_text,
    routes_word,
    signed_pct,
    sweep_view,
    verdict_bands,
    verdict_compare,
    verdict_depot,
    verdict_fleet,
    verdict_losses,
    verdict_optimum_sweep,
    verdict_starts,
    verdict_sweep,
)
from swp_layout import dunkles_design, kopf_css
from swp_pdf_export import build_pdf
from swp_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from swp_visualization import build_bands, build_map, build_start_chart

st.set_page_config(page_title="Sweep und Cluster-first – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _view(settings, k, direction, routing):
    return sweep_view(settings, k, direction, routing)


@st.cache_data(show_spinner=False)
def _band_stats(n, fill, routes):
    return band_stats(band_rows(n, fill, routes))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in swp_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧭 Sweep und Cluster-first")
st.markdown(
    """
**Wo scheitert „erst Gruppen, dann Reihenfolge“?** Der **Sweep** ordnet die Kunden nach dem Winkel um das Depot und füllt in dieser Folge die Fahrzeuge (Stück 3: „Füllen bis voll“); danach bekommt jede Gruppe ihre
eigene Reihenfolge. Das ist **cluster-first, route-second**, die Umkehrung von Stück 4 und 5 (erst Routen zusammenlegen). Die Demo zeigt, was der zweite Schritt, der Start und die Geometrie der Instanz ausmachen,
und stellt den Sweep mit derselben Rundreise je Route neben Savings und Einfügen nach Split.

Weiter unten: **🔬 Der Sweep Schritt für Schritt**, **🔬 Der Start entscheidet**, **🔬 Wo verliert die Gruppenbildung?**, **🔬 Sweep gegen Savings gegen Einfügen nach Split**,
**🔬 Wie schlagen sich die Verfahren?**, **🚧 Wo die Annahmen enden**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So arbeitet der Sweep", expanded=True):
    st.markdown(
        """
1. **Winkelfolge:** Jeder Kunde bekommt den Winkel um das Depot (gegen den Uhrzeigersinn ab Osten); die Kunden werden nach dem Winkel geordnet (Gleichstand: kleinerer Abstand). Die Folge ist ein Kreis.
2. **Start und Richtung:** Man öffnet den Kreis bei einem Startkunden und liest in einer der beiden Richtungen. **Füllen bis voll:** eine neue Route beginnt, sobald der nächste Kunde nicht mehr passt. Das ergibt die **Cluster** (Keile).
3. **Zweiter Schritt:** Je Cluster entweder die Reihenfolge der Winkelfolge oder die **kürzeste Rundreise** (exakt bis 12 Kunden je Cluster, darüber eine Heuristik).
4. **Fairer Vergleich:** Savings und Einfügen nach Split erscheinen auch „+ Rundreise“: jede ihrer Routen neu als kürzeste Rundreise, damit nur die Gruppenbildung verglichen wird.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help=f"Bis n = {C.N_MAX} rechnet die App das exakte Optimum. Größere Instanzen stehen in den vorberechneten Bändern.")
    family = st.selectbox("Art der Karte", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Kleine Karte“: ganze Koordinaten 0 bis 16, Nachfragen 1 bis 4. Die beiden anderen: Karte 0 bis 100, Nachfragen 1 bis 10; „In Gruppen“: drei Häufungen von Kunden.")
    depot = st.selectbox("Lage des Depots", list(range(len(C.DEPOTS))), key="depot_select", format_func=lambda i: C.DEPOTS[i],
                         help="In der Ecke überstreichen die Winkel nur einen Viertelkreis: Die Keile des Sweeps sind dort lang und dünn.")
    routes = st.slider("Zielroutenzahl", *bounds("routes_slider"), key="routes_slider", help="Legt zusammen mit der Auslastung die Kapazität fest; mehr Zielrouten heißt kürzere Routen und dünnere Keile.")
    fill = st.slider("Auslastung (%)", *bounds("fill_slider"), step=C.FILL_STEP, key="fill_slider",
                     help="Kapazität = aufgerundet Gesamtnachfrage geteilt durch (Zielroutenzahl mal Auslastung). Bei hoher Auslastung ist die Kapazität knapp: Der Sweep braucht dann oft mehr Routen als nötig.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "family_select": int(family), "depot_select": int(depot), "routes_slider": int(routes), "fill_slider": int(fill), "seed_input": int(seed)})

settings = Settings(int(n), int(family), int(depot), int(routes), int(fill), int(seed))
a = _analysis(settings)
inst = a.inst
plans = a.plans

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: Gruppen zuerst oder Routen zusammenlegen")
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2). Die Differenz aus den angezeigten, gerundeten Werten, damit Zahl und Delta zusammenpassen.
m1.metric("Optimum (alle Tourenpläne)", de(a.exact.cost), delta="Referenz", delta_color="off")
m2.metric("Sweep, fester Start + Rundreise", de(plans["sw0"].cost), delta=f"{round(plans['sw0'].cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
m3.metric("Sweep, bester Start + Rundreise", de(plans["swb"].cost), delta=f"{round(plans['swb'].cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
m4.metric("Savings (λ = 1) + Rundreise", de(plans["sp1_r"].cost), delta=f"{round(plans['sp1_r'].cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
st.caption(f"Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}, Mindestroutenzahl {a.min_routes}. Das Optimum fährt {routes_word(len(a.exact.routes))}, der Sweep mit festem Start {routes_word(len(plans['sw0'].routes))}, "
           f"mit bestem Start {routes_word(len(plans['swb'].routes))}, Savings {routes_word(len(plans['sp1_r'].routes))}.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a), file_name="sweep-cluster-first.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wo scheitert „erst Gruppen, dann Reihenfolge“?")
kind, text = verdict_compare(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Der Sweep Schritt für Schritt")
st.caption("Die Kunden stehen nach dem Winkel um das Depot in einer Folge; man öffnet den Kreis beim gewählten Startkunden und füllt die Fahrzeuge der Reihe nach. Die gestrichelten Strahlen auf der Karte "
           "sind die Schnitte zwischen den Gruppen, der durchgezogene Strahl markiert den Start.")
e1, e2, e3 = st.columns([2, 2, 2])
with e1:
    k = st.slider("Startposition in der Winkelfolge", 1, inst.n, 1, key=f"start_slider_{inst.n}", help="Position 1 ist der Kunde mit dem kleinsten Winkel (der feste Start).") - 1
with e2:
    direction = 1 if st.radio("Richtung", ["gegen den Uhrzeigersinn", "mit dem Uhrzeigersinn"], key="dir_radio") == "gegen den Uhrzeigersinn" else -1
with e3:
    routing = st.radio("Reihenfolge im Cluster", ["Kürzeste Rundreise", "Winkelfolge"], key="routing_radio") == "Kürzeste Rundreise"
view = _view(settings, int(k), direction, routing)
base_order = W.angular_order(inst)
v1, v2 = st.columns([1, 1])
with v1:
    st.markdown(f"**Sweep: {de(view['plan'].cost)}** ({routes_word(len(view['clusters']))}, {pct(gap_percent(view['plan'].cost, a.exact.cost))} über dem Optimum)")
    st.plotly_chart(build_map(inst, view["plan"].routes, rays=boundary_angles(inst, view["order"], view["clusters"]), start_ray=W.angle_of(inst, view["order"][0])), width="stretch", key="map_sweep")
with v2:
    rows = ["| Platz | Kunde | Winkel | Abstand | Nachfrage | Cluster |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(view["table"], start=1):
        rows.append(f"| {i} | {r['customer']} | {de(r['angle'], 1)}° | {de(r['distance'], 1)} | {r['demand']} | {r['cluster']} |")
    st.markdown("\n".join(rows))
    st.caption("Die Folge ab dem gewählten Start in der gewählten Richtung (bei „mit dem Uhrzeigersinn“ bleibt der Startkunde vorn und der Rest läuft rückwärts).")
kind, text = verdict_sweep(a, int(k), direction, routing, view)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Der Start entscheidet")
st.caption("Dieselbe Instanz, jeder Startkunde und beide Richtungen, jeweils mit Rundreise je Cluster. Die Linien zeigen das Optimum und Savings (λ = 1) mit derselben Rundreise.")
st.plotly_chart(build_start_chart(a.starts, a.exact.cost, plans["sp1_r"].cost), width="stretch", key="start_chart")
kind, text = verdict_starts(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wo verliert die Gruppenbildung?")
st.caption("Drei Verluste lassen sich trennen: Die Gruppen sind nur Stücke der Winkelfolge (Schnittoptimum = beste solche Gruppen mit Rundreise), „Füllen bis voll“ schneidet nach der Kapazität statt nach den Kosten, "
           "und die Winkelfolge ist keine gute Reihenfolge.")
table = ["| Plan | Kosten | über Optimum | Routen |", "|---|---|---|---|"]
table.append(f"| **Optimum** | {de(a.exact.cost)} | {pct(0.0)} | {len(a.exact.routes)} |")
for key in ("cut", "swb", "sw0", "sw0_order", "splitb"):
    p = plans[key]
    table.append(f"| **{C.STRATEGY_NAMES[key]}** | {de(p.cost)} | {pct(gap_percent(p.cost, a.exact.cost))} | {len(p.routes)} |")
st.markdown("\n".join(table))
l1, l2 = st.columns(2)
with l1:
    st.markdown(f"**Optimum: {de(a.exact.cost)}** ({routes_word(len(a.exact.routes))})")
    st.plotly_chart(build_map(inst, a.exact.routes), width="stretch", key="map_optimum")
with l2:
    st.markdown(f"**Schnittoptimum: {de(plans['cut'].cost)}** ({routes_word(len(plans['cut'].routes))})")
    st.plotly_chart(build_map(inst, plans["cut"].routes), width="stretch", key="map_cut")
arcs = ["| Route des Optimums | Kunden | Winkelbereich |", "|---|---|---|"]
for i, r in enumerate(a.opt_arcs, start=1):
    where = f"{de(r['from_deg'], 0)}° bis {de(r['to_deg'], 0)}°" if r["contiguous"] and r["from_deg"] is not None else ("alle Kunden" if r["contiguous"] else "**getrennte Stücke der Winkelfolge**")
    arcs.append(f"| {i} | {order_text(r['route'])} | {where} |")
st.markdown("\n".join(arcs))
kind, text = verdict_losses(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Sweep gegen Savings gegen Einfügen nach Split")
st.caption("Alle Verfahren auf derselben Instanz; „+ Rundreise“ heißt: jede Route neu als kürzeste Rundreise (gleiche Regel für alle). Winkelfolge + Split ist die Winkelfolge als Riesentour aus Stück 1, optimal geschnitten.")
table = ["| Verfahren | Kosten | über Optimum | Routen | gegen Savings + Rundreise |", "|---|---|---|---|---|"]
for key in C.STRATEGY_KEYS:
    p = plans[key]
    vs = "–" if key == C.COMPARE_KEY else signed_pct(diff_percent(p.cost, plans[C.COMPARE_KEY].cost))
    table.append(f"| **{C.STRATEGY_NAMES[key]}** | {de(p.cost)} | {pct(gap_percent(p.cost, a.exact.cost))} | {len(p.routes)} | {vs} |")
st.markdown("\n".join(table))
pa, pb = st.columns(2)
with pa:
    left = st.selectbox("Links", list(C.STRATEGY_KEYS), index=list(C.STRATEGY_KEYS).index("swb"), key="compare_left", format_func=lambda x: C.STRATEGY_NAMES[x])
with pb:
    right = st.selectbox("Rechts", list(C.STRATEGY_KEYS), index=list(C.STRATEGY_KEYS).index("sp1_r"), key="compare_right", format_func=lambda x: C.STRATEGY_NAMES[x])
ma, mb = st.columns(2)
for col, key, chart_key in ((ma, left, "map_left"), (mb, right, "map_right")):
    with col:
        st.markdown(f"**{C.STRATEGY_NAMES[key]}: {de(plans[key].cost)}** ({routes_word(len(plans[key].routes))}, {pct(gap_percent(plans[key].cost, a.exact.cost))} über dem Optimum)")
        st.plotly_chart(build_map(inst, plans[key].routes), width="stretch", key=chart_key)

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie schlagen sich die Verfahren?")
st.caption("Feste Instanzen, vorberechnet (generate_precomputed.py): die Instanzen von Stück 4 und 5, vier Zellen (Kunden zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke), nur Zellen mit Referenz. "
           "Bis 12 Kunden gegen das exakte Optimum, darüber gegen die Referenz PyVRP. Bei 100 Kunden steht der beste Start nur über jede fünfte Startposition.")
short = st.radio("Zielrouten", ["Drei Zielrouten", f"Kurze Routen ({C.SHORT_N} Kunden, {C.SHORT_ROUTES} Zielrouten)"], horizontal=True, key="band_kind") != "Drei Zielrouten"
if short:
    band_n, band_routes, band_fills = C.SHORT_N, C.SHORT_ROUTES, C.SHORT_FILLS
else:
    band_n = int(st.radio("Kunden n", list(C.BAND_SIZES), index=3, horizontal=True, key="band_n"))
    band_routes, band_fills = C.BAND_ROUTES, C.BAND_FILLS[band_n]
band_fill = int(st.radio("Auslastung (%)", list(band_fills), index=list(band_fills).index(90) if 90 in band_fills else 0, horizontal=True, key=f"band_fill_{band_n}_{band_routes}"))
stats = _band_stats(band_n, band_fill, band_routes)
if stats:
    st.caption(f"{instances_word(stats['count'])} (alle vier Zellen zusammen). Die Zahlen sind Spannen über Instanzen, kein Satz.")
    st.plotly_chart(build_bands(stats["gaps"], C.STRATEGY_NAMES, C.STRATEGY_COLORS, C.CHART_KEYS), width="stretch", key="band_chart")
    ref_name = "Optimum" if band_n in C.EXACT_SIZES else "Referenz"
    table = [f"| Verfahren | Median | Minimum bis Maximum | Mittel | trifft {ref_name} | billiger / gleich / teurer als Savings + Rundreise |", "|---|---|---|---|---|---|"]
    for key in stats["keys"]:
        g = stats["gaps"][key]
        vs = "–" if key == C.COMPARE_KEY else (lambda p: f"{p['cheaper']} / {p['equal']} / {p['more']}")(stats["vs"][key])
        table.append(f"| **{C.STRATEGY_NAMES[key]}** | {pct(g['median'])} | {pct(g['min'])} bis {pct(g['max'])} | {pct(g['mean'])} | {g['hit']} von {g['count']} | {vs} |")
    st.markdown("\n".join(table))
    if "cluster_loss" in stats:
        st.caption(f"Zerlegung der Verluste (Median): Cluster-Verlust (Schnittoptimum gegen {ref_name.lower()}) {pct(stats['cluster_loss']['median'])}; Schnitt-Verlust des festen Starts gegen das Schnittoptimum {pct(stats['cut_loss'])}; "
                   f"Routing-Verlust der Winkelfolge gegen die Rundreise je Cluster {pct(stats['routing_loss'])}.")
    st.markdown("**Nach Depot und Kunden** (Median des Abstands: Sweep bester Start + Rundreise / Savings + Rundreise)")
    split = ["| Teilmenge | Sweep, bester Start + Rundreise | Savings + Rundreise |", "|---|---|---|"]
    for d, name in ((0, "Depot in der Mitte"), (1, "Depot in der Ecke")):
        if d in stats["by_depot"] and stats["by_depot"][d]:
            split.append(f"| {name} | {pct(stats['by_depot'][d]['swb'])} | {pct(stats['by_depot'][d]['sp1_r'])} |")
    for f, name in ((1, "Kunden zufällig"), (2, "Kunden in Gruppen")):
        if f in stats["by_family"] and stats["by_family"][f]:
            split.append(f"| {name} | {pct(stats['by_family'][f]['swb'])} | {pct(stats['by_family'][f]['sp1_r'])} |")
    st.markdown("\n".join(split))
kind, text = verdict_bands(band_n, band_fill, band_routes, stats)
getattr(st, kind)(text)
kind, text = verdict_fleet(stats)
getattr(st, kind)(text)
kind, text = verdict_optimum_sweep(stats)
getattr(st, kind)(text)
kind, text = verdict_depot(stats)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Gruppen sind Stücke der Winkelfolge** | Das Optimum nimmt oft Kunden aus getrennten Winkelbereichen in eine Route (zum Beispiel einen Kunden nahe am Depot zu einem fernen Kunden); kein Sweep kann es erreichen | Fisher–Jaikumar (Zuordnung statt Winkel, nicht gebaut) |
| **Keine Flottengrenze** | Bei enger Kapazität braucht der Sweep mehr als die Mindestroutenzahl; mit einer Flottengrenze wäre er dort nicht zulässig | Stück 3 (Split mit Flottengrenze) |
| **Eine Rundreise je Cluster, nichts darüber hinaus** | Keine Verbesserung zwischen den Routen (Austausch, Verschieben von Kunden); die Verfahren bleiben Konstruktion | Demos zu VRP-Nachbarschaften, Fall-Demo „Mini-Tourenplanung“ |
| **Rundreise ab 13 Kunden eine Heuristik** | Die Heuristik liegt nie unter der kürzesten Rundreise, kann aber darüber liegen; alle Verfahren bekommen dieselbe | – |
| **Nur Kapazität, keine Zeitfenster** | Mit Zeitfenstern ist der Winkel nur ein Teil der Ordnung | Stück 8 (Zeitfenster) |
| **Symmetrische Entfernungen** | Mit asymmetrischen Entfernungen ändert Umdrehen einer Route die Länge | – |
| **Referenz PyVRP ab 25 Kunden** | Eine gute Lösung, keine bewiesene Untergrenze | – |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    n12 = 12
    st.markdown(
        r"""
**Lesehilfe.** Wie in den Stücken 1 bis 5: Ein Depot $0$, Kunden $1, \dots, n$ mit Nachfragen $q_i$, Kapazität $Q$, euklidische Entfernungen.

| Symbol | Bedeutung |
|---|---|
| $\varphi_i \in [0, 2\pi)$ | Polarwinkel des Kunden $i$ um das Depot (Kunde auf dem Depot: $0$) |
| $\sigma = (\sigma_1, \dots, \sigma_n)$ | die Winkelfolge: Kunden nach $\varphi$, Gleichstand: kleinerer Abstand, dann kleinere Nummer; zyklisch |
| $\sigma^{(k, \pm)}$ | die bei Position $k$ geöffnete Folge, gelesen in Richtung $+$ oder $-$ |
| $T(C)$ | Länge der kürzesten Rundreise durch das Depot und alle Kunden der Gruppe $C$ |

**Sweep.** Schneide $\sigma^{(k, \pm)}$ durch „Füllen bis voll“ in aufeinanderfolgende Gruppen $C_1, \dots, C_g$ (Stück 3: $g$ ist die kleinste Zahl aufeinanderfolgender Gruppen, in die die Folge passt) und fahre jede Gruppe als Rundreise: Länge $\sum_r T(C_r)$. Der beste Start ist das Minimum über alle $2n$ Starts.

**Schnittoptimum.** $\min \sum_r T(C_r)$ über alle Zerlegungen der zyklischen Folge in zusammenhängende Gruppen mit Last $\le Q$; für jede Startposition und Richtung ein kürzester Weg im Hilfsgraphen von Stück 1 mit den Bogenkosten $T(\sigma_{i+1}, \dots, \sigma_j)$.

**Satz (wie viele Gruppierungen sieht der Sweep?).** Eine Zerlegung eines Kreises aus $n$ Kunden in $k \ge 2$ zusammenhängende Gruppen ist durch $k$ der $n$ Lücken zwischen Nachbarn bestimmt: es gibt $\binom{n}{k}$ davon, und für $k = 1$ gibt es genau eine. Alle Zerlegungen der Kundenmenge in $k$ nichtleere Gruppen sind die Stirling-Zahlen zweiter Art $S(n, k)$. Für $n = """ + str(n12) + r""", k = 3$ sind das $""" + f"{math.comb(n12, 3)}" + r"""$ gegen $""" + f"{W.stirling2(n12, 3):,}".replace(",", "\\,") + r"""$. Die Zahlen sind an kleinen $n$ gegen die Aufzählung geprüft (Tests); die Kapazität lässt noch weniger zu.

**Warum der Sweep scheitert, wenn er scheitert.** Hat das Optimum eine Route, deren Kunden in der Winkelfolge nicht zusammenhängen, ist es keine Sweep-Zerlegung, und kein Start und keine Rundreise kann es erreichen: das ist der *Cluster-Verlust*. Dazu kommt der *Schnitt-Verlust* („Füllen bis voll“ schneidet nach der Last, nicht nach den Kosten) und der *Routing-Verlust* (die Winkelfolge als Route). Die Demo trennt die drei an den Instanzen; ein Satz über ihre Größe wird nicht behauptet.

**Winkelfolge als Riesentour.** Die Winkelfolge ist eine Reihenfolge aller Kunden; mit optimalem Split (Stück 1) bleibt sie eine schwache Riesentour, weil benachbarte Kunden im Winkel weit auseinander liegen können (Abstand zum Depot): ein Zickzack zwischen innen und außen.

**Literatur.** Der Sweep geht laut Abstract auf Gillett und Miller (1974) zurück; die Zuordnungsheuristik („cluster-first“ mit verallgemeinertem Zuordnungsproblem) auf Fisher und Jaikumar (1981); „route first, cluster second“ (die Grundlage des Splits) auf Beasley (1983); die Mehrfachrouten-Auswahl „Petal“ auf Ryan, Hjorring und Glover (1993). Alle wurden nur als Abstract oder Suchtreffer gesehen; die Demo übernimmt keine Zahl daraus. Das Schnittoptimum ist nach dem Namen ein Petal mit Sektoren; die Gleichsetzung ist ungeprüft.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
