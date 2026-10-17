#!/usr/bin/env python3
"""diagnostica_grib.py - controlla la struttura dei GRIB2 scritti da scarica_icon2i.py (come li leggerebbe ungrib)."""
import sys
from pathlib import Path

import eccodes as ec


def sezioni(d, pos):
    """Elenco (numero, lunghezza) delle sezioni del messaggio che inizia a pos."""
    out, p = [], pos + 16
    while d[p:p + 4] != b"7777":
        n = int.from_bytes(d[p:p + 4], "big")
        out.append((d[p + 4], n))
        p += n
    return out, p + 4


def main():
    cart = Path(sys.argv[1])
    files = sorted(cart.glob("*.grib2"))
    print(len(files), "file:", [f.name for f in files][:3], "...")
    for f in files[:2]:
        d = f.read_bytes()
        print(f"== {f.name}: {len(d)} byte, inizio {d[:16].hex()}")
        pos, n, insiemi = 0, 0, {}
        while pos < len(d):
            if d[pos:pos + 4] != b"GRIB":
                print(f"  !! alla posizione {pos} non c'e' GRIB: {d[pos:pos + 8]!r}")
                break
            lung = int.from_bytes(d[pos + 8:pos + 16], "big")
            sz, fine = sezioni(d, pos)
            if fine - pos != lung:
                print(f"  !! messaggio {n}: lunghezza dichiarata {lung}, reale {fine - pos}")
            insiemi.setdefault(tuple(sz), 0)
            insiemi[tuple(sz)] += 1
            if n == 0:
                print("  ottetto 8 (edizione):", d[pos + 7], " disciplina:", d[pos + 6])
            pos += lung
            n += 1
        print(f"  {n} messaggi; strutture delle sezioni (numero, lunghezza):")
        for k, v in insiemi.items():
            print("   ", v, "x", k)
        with open(f, "rb") as fh:
            h = ec.codes_grib_new_from_file(fh)
            for k in ("editionNumber", "centre", "subCentre", "gridDefinitionTemplateNumber", "productDefinitionTemplateNumber",
                      "dataRepresentationTemplateNumber", "PVPresent", "numberOfValues", "bitsPerValue", "significanceOfReferenceTime",
                      "typeOfGeneratingProcess", "dataDate", "dataTime", "stepUnits", "forecastTime", "Ni", "Nj", "shapeOfTheEarth",
                      "iScansNegatively", "jScansPositively", "jPointsAreConsecutive", "resolutionAndComponentFlags",
                      "latitudeOfFirstGridPointInDegrees", "longitudeOfFirstGridPointInDegrees", "iDirectionIncrementInDegrees"):
                try:
                    print("   ", k, ec.codes_get(h, k))
                except Exception as e:
                    print("   ", k, "ERR", type(e).__name__)


if __name__ == "__main__":
    main()
