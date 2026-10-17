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


def main():
    hub = s.Hub()
    ciclo = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
    ora = 6
    fs = hub.elenco(s.SUPERFICIE)
    nomi = ["Temperature (K)", "Dewpoint temperature (K)", "u-component of wind (m/s)", "v-component of wind (m/s)", "Pressure (Pa)",
            "Pressure reduced to MSL (Pa)", "Snow depth water equivalent (kg m-2)", "Snow depth (m)", "Soil temperature (K)",
            "Column-integrated soil moisture (kg m-2)", "Land cover (0 = sea, 1 = land) (Proportion)", "Geopotential (m2 s-2)",
            "Geometric height (m)"]
    prod = [p for p in fs["product"] if p["desc"] in nomi]
    elenca(hub.estrai(s.SUPERFICIE, ciclo, {"product": prod, "timerange": s.tempo(fs["timerange"], ora)}, "ispez_sup"),
           "SUPERFICIE: prodotti scelti, tutti i livelli, +6 h")
    fm = hub.elenco(s.MODELLO)
    lv = [l for l in fm["level"] if l.get("level_type") == 150 and l["value"] in (1, 33, 65, 66)]
    prod = [p for p in fm["product"] if p["desc"] in ("Temperature (K)", "Pressure (Pa)", "Geometric height (m)", "Specific humidity (kg/kg)")]
    elenca(hub.estrai(s.MODELLO, ciclo, {"product": prod, "level": lv, "timerange": s.tempo(fm["timerange"], ora)}, "ispez_mod"),
           "MODELLO: T, p, z, q a 4 livelli, +6 h")


if __name__ == "__main__":
    main()
