#!/usr/bin/env python3
"""ispeziona_icon2i.py - elenca i messaggi che MeteoHub restituisce per superficie, suolo e livelli del modello (un istante)."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import eccodes as ec

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scarica_icon2i as s  # noqa: E402


def elenca(dati, titolo, tutti=True):
    print(f"=== {titolo}: {len(dati) / 1e6:.1f} MB")
    for h in s.messaggi(dati):
        g = lambda k: ec.codes_get(h, k) if ec.codes_is_defined(h, k) else "-"
        v = ec.codes_get_values(h)
        print(f"d{g('discipline')} c{g('parameterCategory')} n{g('parameterNumber')} {g('shortName'):>10} | {g('name')[:48]:48} | lev1 t{g('typeOfFirstFixedSurface')} "
              f"sc{g('scaleFactorOfFirstFixedSurface')} v{g('scaledValueOfFirstFixedSurface')} | lev2 t{g('typeOfSecondFixedSurface')} "
              f"v{g('scaledValueOfSecondFixedSurface')} | step {g('stepRange')} | {v.min():.4g}..{v.max():.4g} | {g('packingType')}", flush=True)
        ec.codes_release(h)


def passi(dati):
    out = []
    for h in s.messaggi(dati):
        out.append(ec.codes_get(h, "stepRange"))
        ec.codes_release(h)
    return out


def main():
    hub = s.Hub()
    ciclo = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
    fm = hub.elenco(s.MODELLO)
    lv = [l for l in fm["level"] if l.get("level_type") == 150 and l["value"] in (33,)]
    prod = [p for p in fm["product"] if p["desc"] in ("Temperature (K)",)]
    d = hub.estrai(s.MODELLO, ciclo, {"product": prod, "level": lv}, "ispez_passi_mod")
    print("MODELLO T livello 33, tutti i tempi:", len(passi(d)), passi(d))
    fs = hub.elenco(s.SUPERFICIE)
    prod = [p for p in fs["product"] if p["desc"].startswith("Land cover")]
    d = hub.estrai(s.SUPERFICIE, ciclo, {"product": prod}, "ispez_landcover")
    print("LAND COVER, tutti i tempi:", len(passi(d)))
    elenca(d[:3_000_000] if len(d) > 3_000_000 else d, "land cover (primi messaggi)")
    prod = [p for p in fs["product"] if p["desc"].startswith("Geopotential")]
    lv = [l for l in fs["level"] if "desc" in l and l["desc"].startswith("sfc Ground or water surface 0 0")]
    d = hub.estrai(s.SUPERFICIE, ciclo, {"product": prod, "level": lv}, "ispez_geopot")
    print("GEOPOTENZIALE al suolo:", len(passi(d)), passi(d)[:5])


if __name__ == "__main__":
    main()
