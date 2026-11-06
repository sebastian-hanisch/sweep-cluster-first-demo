"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 12, 8
SEED_MAX, DEFAULT_SEED = 999999, 0
ROUTES_MIN, ROUTES_MAX, DEFAULT_ROUTES = 2, 4, 3
FILL_MIN, FILL_MAX, FILL_STEP, DEFAULT_FILL = 60, 100, 2, 90   # Auslastung in Prozent: Kapazität = aufgerundet Gesamtnachfrage / (Zielroutenzahl · Auslastung)
CLUSTERS, CLUSTER_SIGMA = 3, 7.0              # Familie „In Gruppen“
FAMILIES = ("Kleine Karte (ganze Zahlen)", "Zufällig verteilt (0 bis 100)", "In Gruppen (0 bis 100)")
FAMILY_KEYS = ("small", "random", "clustered")
DEFAULT_FAMILY = 1
DEPOTS = ("In der Mitte", "In der Ecke")
DEFAULT_DEPOT = 0

# Verfahren im Vergleich (Experiment 4 und Bänder): Schlüssel und Namen. „+ Rundreise“: jede Route des Plans neu als kürzeste Rundreise (gleiche Regel für alle Verfahren).
STRATEGY_KEYS = ("sw0_order", "sw0", "swb_order", "swb", "splitb", "cut", "sp1", "sp1_r", "lam9_r", "es", "es_r")
STRATEGY_NAMES = {
    "sw0_order": "Sweep, fester Start, Winkelfolge",
    "sw0": "Sweep, fester Start + Rundreise",
    "swb_order": "Sweep, bester Start, Winkelfolge",
    "swb": "Sweep, bester Start + Rundreise",
    "splitb": "Winkelfolge + Split (bester Start)",
    "cut": "Schnittoptimum (beste Cluster + Rundreise)",
    "sp1": "Savings, λ = 1",
    "sp1_r": "Savings, λ = 1 + Rundreise",
    "lam9_r": "Bestes von 9 λ + Rundreise",
    "es": "Einfügen nach Split",
    "es_r": "Einfügen nach Split + Rundreise",
}
CHART_KEYS = ("sw0", "swb", "splitb", "cut", "sp1_r", "lam9_r", "es_r")       # im Balkendiagramm der Bänder
COMPARE_KEY = "sp1_r"                         # die gepaarten Zählungen der Bänder vergleichen mit Savings λ = 1 + Rundreise
TOL = 1e-9                                    # Gleichstände und Gleichheit von Kosten: absolut
TIE = 1e-12                                   # Beim Einfügen zählt ein Kandidat nur als besser, wenn er um mehr als TIE besser ist
GAP_WARN = 5.0                                # Abstand in Prozent, ab dem das Verdikt warnt
LEVEL_PP = 1.0                                # „gleichauf“: Unterschied der Mediane unter einem Prozentpunkt

# Bänder (vorberechnet, swp_bands.json): feste Instanzen der Stück-4/5-Demos, vier Zellen (Kunden zufällig/Gruppen mal Depot Mitte/Ecke), nur Zellen mit Referenz
BAND_FILE = "swp_bands.json"
BAND_SIZES = (10, 12, 25, 50, 100)
BAND_FILLS = {10: (90,), 12: (60, 75, 90, 98), 25: (90,), 50: (90,), 100: (90,)}
BAND_CELLS = ((1, 0), (2, 0), (1, 1), (2, 1))
BAND_ROUTES = 3
SHORT_N, SHORT_ROUTES, SHORT_FILLS = 50, 8, (90, 98)     # kurze Routen: 50 Kunden, 8 Zielrouten
EXACT_SIZES = (10, 12)                        # Referenz = exaktes Optimum; sonst PyVRP (5 s, ein Seed)
BAND_SEEDS = {10: tuple(range(300000, 300020)), 12: tuple(range(300000, 300020)), 25: tuple(range(300000, 300008)), 50: tuple(range(300000, 300008)), 100: tuple(range(300000, 300008))}
BAND_START_STEP = {100: 5}                    # bei 100 Kunden nur jede fünfte Startposition (beide Richtungen); sonst alle
CUT_MAX_N = 25                                # das Schnittoptimum steht in den Bändern bis zu dieser Größe
ES_R_MAX_N = 50                               # Einfügen nach Split + Rundreise steht in den Bändern bis zu dieser Größe
SOURCE_BANDS_FILE = "svv_bands.json"          # Quelle der Instanzen, Referenzen und der Savings- und Einfügen-nach-Split-Kosten (savings-varianten-demo, Stück 5)

COLOR_SWEEP = "#d8a13a"
COLOR_OPT = "#c0504d"
COLOR_SAVINGS = "#2F6B65"
ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b", "#17becf", "#e377c2")
STRATEGY_COLORS = {"sw0_order": "#e6c27a", "sw0": "#d8a13a", "swb_order": "#c9a98a", "swb": "#b5651d", "splitb": "#999999", "cut": "#7b5ea7", "sp1": "#7fb3ad",
                   "sp1_r": "#2F6B65", "lam9_r": "#17becf", "es": "#9ab6d9", "es_r": "#4c78a8"}

# Presets (Instanzen aus der Suche; die Zahlen in den Hilfetexten prüft tests/test_claims.py)
PRESETS = {
    "Das Optimum ist keine Sweep-Zerlegung (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 0},
    "Ein Kunde nahe am Depot sprengt den Keil (n = 6)": {"n": 6, "family": 0, "depot": 1, "routes": 2, "fill": 90, "seed": 13},
    "Der Start entscheidet (n = 8, Depot in der Ecke)": {"n": 8, "family": 1, "depot": 1, "routes": 3, "fill": 90, "seed": 6},
    "Die Winkelfolge allein trifft das Optimum (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 1},
    "Enge Kapazität: mehr Routen als nötig (n = 12, 98 %)": {"n": 12, "family": 1, "depot": 0, "routes": 3, "fill": 98, "seed": 11},
}
PRESET_HELP = {
    "Das Optimum ist keine Sweep-Zerlegung (n = 8)": "Einfügen nach Split trifft das Optimum 444,40, das aber keine Sweep-Zerlegung ist; der Sweep mit festem Start kostet 517,11 (+16,4 %), der beste Start und das Schnittoptimum je 492,17 (+10,8 %).",
    "Ein Kunde nahe am Depot sprengt den Keil (n = 6)": "Das Optimum 77,79 hat die Routen (2 6 1 4) und (3 5): Kunde 5 liegt nahe am Depot im Winkelbereich der Kunden 4 und 1, gehört aber zum fernen Kunden 3. Sweep mit festem Start 93,73 (+20,5 %), bester Start 91,54 (+17,7 %); Savings und Einfügen nach Split treffen das Optimum.",
    "Der Start entscheidet (n = 8, Depot in der Ecke)": "Das Optimum 703,27 ist eine Sweep-Zerlegung. Der feste Start braucht 4 statt 3 Routen und kostet 843,89 (+20,0 %), der beste von 16 Starts trifft das Optimum, der schlechteste liegt 29,4 % darüber; Savings mit Rundreise trifft es ebenfalls.",
    "Die Winkelfolge allein trifft das Optimum (n = 8)": "Hier trifft schon die Winkelfolge je Route das Optimum 380,72 (mit Rundreise je Cluster und mit bestem Start ebenso); Savings liegt 3,3 % darüber.",
    "Enge Kapazität: mehr Routen als nötig (n = 12, 98 %)": "Bei 98 % Auslastung braucht der Sweep mit festem Start 4 statt der Mindestroutenzahl 3 (16 von 24 Starts brauchen mehr als 3). Er liegt 13,3 % (fester Start) und 10,7 % (bester Start) über dem Optimum 447,47; Einfügen nach Split trifft es.",
}

# Text des Expanders „Annahmen, Grenzen und bekannte Probleme“; derselbe Text steht in der README (tests/test_readme.py vergleicht beide)
ASSUMPTIONS_MARKDOWN = """**Annahmen**
- Ein Depot, beliebig viele gleiche Fahrzeuge (die Flottengrenze fehlt), euklidische und symmetrische Entfernungen, keine Zeitfenster; jeder Kunde wird genau einmal von einem Fahrzeug bedient, seine Nachfrage ist nicht teilbar.
- Alles ist simuliert: Karten aus Zufallszahlen, kein Straßennetz, keine echten Aufträge.
- „Sweep“ meint die Fassung mit Winkelfolge um das Depot, „Füllen bis voll“ als Schnitt und einem Startkunden (beide Richtungen); das Depot bestimmt den Winkel, ein Kunde auf dem Depot hat per Setzung den Winkel 0. Das Verfahren ist nach Sekundärquellen übernommen (Gillett und Miller, 1974), nicht an der Originalarbeit geprüft.
- „Rundreise je Cluster“ meint die kürzeste Rundreise durch das Depot und alle Kunden des Clusters: exakt bis 12 Kunden, darüber eine Heuristik (2-opt und Or-opt ab der Winkelfolge, nie unter der kürzesten Rundreise). Savings und Einfügen nach Split bekommen für den Vergleich dieselbe Regel („+ Rundreise“).

**Grenzen**
- Live rechnet die App bis zu 12 Kunden mit exaktem Optimum. Die Bänder gelten für 10 und 12 Kunden (exaktes Optimum, je 80 feste Instanzen) und für 25, 50 und 100 Kunden (je 32 feste Instanzen, Referenz PyVRP, nicht bewiesen optimal) bei drei Zielrouten sowie für 50 Kunden mit 8 Zielrouten; nur Zellen mit Referenz.
- Bei 100 Kunden steht der beste Start nur über jede fünfte Startposition (beide Richtungen); das Schnittoptimum steht bis 25 Kunden, Einfügen nach Split + Rundreise bis 50 Kunden.
- Die Referenz PyVRP (5 Sekunden, ein Seed) ist eine gute Lösung, keine Untergrenze: Abstände zur Referenz sind keine Abstände zum Optimum.
- Der Sweep ist ohne Flottengrenze gerechnet; „braucht mehr als die Mindestroutenzahl“ zählt, wie oft er bei einer Flottengrenze in Höhe der Mindestroutenzahl nicht zulässig wäre.
- Das Schnittoptimum ist nach dem Namen ein Sektor-Petal (Ryan, Hjorring und Glover, 1993); die Gleichsetzung ist nicht geprüft. Fisher–Jaikumar ist nicht gebaut.

**Bekannte Probleme und Unsicherheiten**
- Die Bänder sind Spannen über feste Instanzen, keine Trends und keine Aussagen über andere Kartenarten oder Zielroutenzahlen; zu n steht keine Trendaussage in der App.
- Die Rundreise je Cluster ist ab 13 Kunden eine Heuristik; der Vergleich mit Savings und Einfügen nach Split nutzt dieselbe Regel, nicht eine bessere.
- Der Winkel bestimmt die Folge; bei Kunden auf einer Geraden durch das Depot entscheidet der Abstand, dann die Nummer, und bei Rundungsfehlern können Gleichstände anders ausfallen.
- Die Rechenzeiten (Größenordnung) sind eine Messung unter Windows, nicht festgeschrieben.
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft."""
