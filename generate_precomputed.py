"""Erzeugt swp_bands.json: die Bänder über feste Instanzen (Sweep, Winkelfolge + Split, Schnittoptimum, Savings und Einfügen nach Split mit Rundreise je Route).

Die Instanzen, die Referenzen (exaktes Optimum bis 12 Kunden, PyVRP 0.14.1 darüber) und die Kosten von Einfügen nach Split und von Savings (λ = 1 und bestes von 9) stammen aus svv_bands.json der
savings-varianten-demo (Stück 5 der Linie, Ordner daneben). Je Instanz rechnet dieses Skript: Sweep mit festem Start und mit bestem Start (Winkelfolge und Rundreise je Cluster), Winkelfolge + Split,
das Schnittoptimum (bis 25 Kunden), Savings und Einfügen nach Split (bis 50 Kunden) mit Rundreise je Route, Routenzahlen gegen die Mindestroutenzahl und (bis 12 Kunden) ob das exakte Optimum eine
Sweep-Zerlegung ist. Bei 100 Kunden steht der beste Start nur über jede fünfte Startposition (siehe swp_constants.BAND_START_STEP). PyVRP wird hier nicht gebraucht.

Aufruf (Teile können parallel laufen; `--cells` wählt Zellen nach ihrem Platz in BAND_CELLS):
    python generate_precomputed.py cells 12 3 60 75 90 98 --out part_12.json     # Größe, Zielrouten, Auslastungen in Prozent
    python generate_precomputed.py cells 100 3 90 --cells 0 --out part_100_0.json
    python generate_precomputed.py merge part_*.json                              # zu swp_bands.json zusammenführen"""

import argparse
import json
import time
from pathlib import Path

import swp_constants as C
from swp_evaluation import instance_row

TARGET = Path(__file__).with_name(C.BAND_FILE)
SOURCE = Path(__file__).resolve().parent.parent / "savings-varianten-demo" / C.SOURCE_BANDS_FILE


def source_cells() -> dict:
    """{(n, Zielrouten, Auslastung, Familie, Depot): {Seed: (Referenz, Einfügen nach Split, Savings λ = 1, bestes Savings von 9)}}."""
    out = {}
    for c in json.loads(SOURCE.read_text(encoding="utf-8"))["cells"]:
        out[(c["n"], c["routes"], c["fill"], c["family"], c["depot"])] = {r["seed"]: (r["ref"], r["es"], r["par"]["1.0"], min(r["par"].values())) for r in c["rows"]}
    return out


def build(n: int, routes: int, fills, cells_idx) -> list[dict]:
    cells, start, src = [], time.time(), source_cells()
    for fill in fills:
        for idx, (family, depot) in enumerate(C.BAND_CELLS):
            if cells_idx is not None and idx not in cells_idx:
                continue
            refs = src[(n, routes, fill, family, depot)]
            rows = [instance_row(n, family, depot, routes, seed, fill, *refs[seed]) for seed in C.BAND_SEEDS[n]]
            cells.append({"n": n, "fill": fill, "routes": routes, "family": family, "depot": depot, "rows": rows})
            print("cells", n, routes, fill, family, depot, f"{time.time() - start:.0f} s", flush=True)
    return cells


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["cells", "merge"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--cells", help="Platz der Zellen in BAND_CELLS, getrennt durch Kommas (Voreinstellung: alle vier)")
    args = ap.parse_args()
    if args.kind == "merge":
        cells = []
        for f in args.args:
            cells += json.loads(Path(f).read_text(encoding="utf-8"))["cells"]
        key = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
        cells.sort(key=lambda c: (c["routes"], c["n"], c["fill"], key[(c["family"], c["depot"])]))
        meta = {"seeds": {str(n): [s[0], s[-1]] for n, s in C.BAND_SEEDS.items()}, "start_step": {str(n): s for n, s in C.BAND_START_STEP.items()}, "exact_max": 12,
                "source": f"Instanzen, Referenzen, Einfügen nach Split und Savings aus {C.SOURCE_BANDS_FILE} (savings-varianten-demo, Stück 5)"}
        TARGET.write_text(json.dumps({"meta": meta, "cells": cells}, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", TARGET.name, len(cells), "Zellen")
    else:
        idx = None if args.cells is None else {int(x) for x in args.cells.split(",")}
        data = {"cells": build(int(args.args[0]), int(args.args[1]), [int(x) for x in args.args[2:]], idx)}
        Path(args.out).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", args.out)
