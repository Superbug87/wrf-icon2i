#!/usr/bin/env python3
"""ispeziona_quota.py - cerca dove MeteoHub mette la quota dei livelli del modello (Geometric height)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scarica_icon2i as s  # noqa: E402
from ispeziona_icon2i import elenca  # noqa: E402


def main():
    hub = s.Hub()
    ciclo = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
    fm = hub.elenco(s.MODELLO)
    print("prodotti con height/geopotential/level:")
    for p in fm["product"]:
        if any(x in p["desc"].lower() for x in ("height", "geopotential", "thickness", "level")):
            print("  ", json.dumps(p))
    tipi = {}
    for l in fm["level"]:
        tipi.setdefault((l.get("level_type"), l.get("style"), l.get("l1"), l.get("l2")), []).append(l)
    print("tipi di livello:")
    for k, v in tipi.items():
        print("  ", k, len(v), json.dumps(v[0])[:200], "...", json.dumps(v[-1])[:200])
    prod = [p for p in fm["product"] if p["desc"].startswith("Geometric height")]
    liv = [l for l in fm["level"] if l.get("style") == "GRIB2D" and l.get("l1") == 150 and 60 <= l.get("value1", 0) <= 65]
    d = hub.estrai(s.MODELLO, ciclo, {"product": prod, "level": liv, "timerange": s.tempo(fm["timerange"], 0)}, "ispez_zfull")
    elenca(d, "quota ultimi livelli (strati)")
    fs = hub.elenco(s.SUPERFICIE)
    print("superficie, prodotti con geopotential/orography/height/elevation/terrain:")
    for p in fs["product"]:
        if any(x in p["desc"].lower() for x in ("geopotential", "orograph", "height", "elevation", "terrain", "altitude")):
            print("  ", json.dumps(p))
    print("superficie, livelli sfc:")
    for l in fs["level"]:
        if "desc" in l and l["desc"].lower().startswith(("sfc", "1 ", "103", "0 ")):
            print("  ", l["desc"])


if __name__ == "__main__":
    main()
