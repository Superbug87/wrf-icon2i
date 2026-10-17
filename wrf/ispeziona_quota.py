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
    liv = [l for l in fm["level"] if l.get("level_type") == 150 and l.get("value") is not None]
    print("timerange disponibili:", [t["desc"] for t in fm["timerange"]][:12], "...", len(fm["timerange"]))
    for nome, filtri, c in (
            ("senza_timerange_12", {"product": prod, "level": liv}, ciclo),
            ("senza_timerange_00", {"product": prod, "level": liv}, ciclo.replace(hour=0)),
            ("senza_livelli_12", {"product": prod}, ciclo)):
        d = hub.estrai(s.MODELLO, c, filtri, "ispez_" + nome)
        print("###", nome, f"{len(d) / 1e6:.1f} MB")
        if d:
            elenca(d[:30_000_000], nome)
            break


if __name__ == "__main__":
    main()
