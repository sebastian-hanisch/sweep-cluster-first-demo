"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import swp_constants as C
from swp_evaluation import Analysis, Settings, de, gap_percent, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Sweep und Cluster-first"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Kunden, Karte: {C.FAMILIES[s.family]}, Depot: {C.DEPOTS[s.depot].lower()}, Zielroutenzahl {s.routes}, Auslastung {s.fill} %, Seed {s.seed}. "
                            f"Kapazität {a.inst.capacity}, Gesamtnachfrage {sum(a.inst.demand)}, Mindestroutenzahl {a.min_routes}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (82, 26, 36, 30)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Verfahren", "Kosten", "Über Optimum", "Routen")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    rows = [("Optimum (alle Tourenpläne)", a.exact.cost, len(a.exact.routes))]
    rows += [(C.STRATEGY_NAMES[k], a.plans[k].cost, len(a.plans[k].routes)) for k in C.STRATEGY_KEYS]
    for name, cost, k in rows:
        for w, v in zip(widths, (name, de(cost), pct(gap_percent(cost, a.exact.cost)), str(k))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Sweep: Starts"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    costs = [r["cost"] for r in a.starts]
    pdf.multi_cell(0, 5, _s(f"{len(costs)} Starts (Position und Richtung), jeweils mit Rundreise je Cluster: bester {de(min(costs))}, fester Start {de(costs[0])}, schlechtester {de(max(costs))}. "
                            f"Das Optimum {'ist' if a.opt_sweep else 'ist keine'} Sweep-Zerlegung."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Der Sweep ordnet die Kunden nach dem Winkel um das Depot und füllt die Fahrzeuge in dieser Folge; die Rundreise je Cluster ist exakt bis 12 Kunden, darüber eine Heuristik. "
                            "Savings und Einfügen nach Split bekommen dieselbe Rundreise je Route. Quelle: sweep-cluster-first-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
