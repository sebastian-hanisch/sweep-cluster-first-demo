"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import swp_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, routes, title_prefix="Route", rays=None, start_ray=None):
    """Karte: Depot als Quadrat, Kunden als Kreise (Größe = Nachfrage, Beschriftung = Nummer), jede Route eine Farbe. `rays`: Winkel (Bogenmaß) der Schnitte zwischen den Clustern als gestrichelte
    Strahlen vom Depot, `start_ray`: Winkel des Startkunden (durchgezogener grauer Strahl). Gleicher Maßstab in x und y über scaleanchor mit autorange; der Rand kommt von zwei unsichtbaren Eckmarken."""
    xs = [p[0] for p in inst.xy]
    ys = [p[1] for p in inst.xy]
    pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    reach = 1.15 * max(math.dist(inst.xy[0], p) for p in inst.xy[1:]) if inst.n else 1.0
    for angle, dash, name in [(a, "dot", "Schnitt") for a in (rays or [])] + ([(start_ray, "solid", "Start")] if start_ray is not None else []):
        fig.add_trace(go.Scatter(x=[inst.xy[0][0], inst.xy[0][0] + reach * math.cos(angle)], y=[inst.xy[0][1], inst.xy[0][1] + reach * math.sin(angle)], mode="lines",
                                 line=dict(color="rgba(120,120,120,0.55)", width=1.5, dash=dash), hoverinfo="skip", showlegend=False))
    for r, route in enumerate(routes):
        pts = [inst.xy[0]] + [inst.xy[c] for c in route] + [inst.xy[0]]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)], width=3),
                                 name=f"{title_prefix} {r + 1} (Last {inst.load(route)} von {inst.capacity})", hoverinfo="skip"))
    customers = list(range(1, inst.n + 1))
    fig.add_trace(go.Scatter(
        x=[inst.xy[c][0] for c in customers], y=[inst.xy[c][1] for c in customers], mode="markers+text", text=[str(c) for c in customers], textposition="top center",
        marker=dict(size=[9 + 2.5 * inst.demand[c - 1] for c in customers], color="rgba(150,150,150,0.55)", line=dict(color="#555", width=1)),
        customdata=[[inst.demand[c - 1]] for c in customers], hovertemplate="Kunde %{text}: Nachfrage %{customdata[0]}<extra></extra>", name="Kunden (Größe = Nachfrage)"))
    fig.add_trace(go.Scatter(x=[inst.xy[0][0]], y=[inst.xy[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, 380)


def _hline(fig, y, text, color, dash="dot"):
    fig.add_hline(y=y, line=dict(color=color, width=1.5, dash=dash), annotation_text=text, annotation_position="top left", annotation_font_size=11)


def build_start_chart(starts, optimum, savings_cost):
    """Kosten (mit Rundreise je Cluster) über der Startposition, je eine Linie je Richtung; Linien: Optimum und Savings (λ = 1) mit Rundreise."""
    fig = go.Figure()
    for direction, name, color, dash in ((1, "gegen den Uhrzeigersinn", C.COLOR_SWEEP, "solid"), (-1, "mit dem Uhrzeigersinn", "#4c78a8", "dash")):
        rows = [r for r in starts if r["direction"] == direction]
        fig.add_trace(go.Scatter(x=[r["k"] + 1 for r in rows], y=[r["cost"] for r in rows], mode="lines+markers", name=name, line=dict(color=color, width=3, dash=dash), marker=dict(size=7),
                                 customdata=[[r["routes"]] for r in rows], hovertemplate="Start %{x}: %{y:.2f} (%{customdata[0]} Routen)<extra>" + name + "</extra>"))
    _hline(fig, optimum, f"Optimum {optimum:.2f}", C.COLOR_OPT)
    _hline(fig, savings_cost, f"Savings + Rundreise {savings_cost:.2f}", C.COLOR_SAVINGS, "dash")
    fig.update_xaxes(title_text="Startposition in der Winkelfolge", dtick=1)
    fig.update_yaxes(title_text="Gesamtlänge")
    fig = _base(fig, 380)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=60), legend=dict(orientation="h", y=-0.28))
    return fig


def build_bands(gaps_by_key, names, colors, keys):
    """Median des Abstands zur Referenz in Prozent je Verfahren, mit Spanne (Minimum bis Maximum) als Fehlerbalken."""
    keys = [k for k in keys if k in gaps_by_key]
    fig = go.Figure(go.Bar(
        x=[names[k] for k in keys], y=[gaps_by_key[k]["median"] for k in keys], marker_color=[colors[k] for k in keys],
        error_y=dict(type="data", symmetric=False, array=[gaps_by_key[k]["max"] - gaps_by_key[k]["median"] for k in keys], arrayminus=[gaps_by_key[k]["median"] - gaps_by_key[k]["min"] for k in keys]),
        hovertemplate="%{x}: Median %{y:.1f} %<extra></extra>", name="Median (Balken: Minimum bis Maximum)"))
    fig.update_yaxes(title_text="Abstand zur Referenz (%)", rangemode="tozero")
    fig.update_xaxes(tickangle=-25)
    fig = _base(fig, 420)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=140))
    return fig
