#!/usr/bin/env python3
"""ispeziona_quota.py - elenca i campi di superficie e suolo (un istante) con tipo e valore dei livelli."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scarica_icon2i as s  # noqa: E402


def main():
    hub = s.Hub()
    ciclo = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
    campi, _ = s.superficie_tutti(hub, ciclo, [0])
    visti = {}
    for k, v in campi:
        visti.setdefault(k[:7], []).append(v)
    print(f"{len(campi)} campi, {len(visti)} chiavi (disc, cat, num, tipo1, val1, tipo2, val2):")
    for k in sorted(visti):
        v = visti[k][0]
        print("  ", k, f"{np.nanmin(v):.4g}..{np.nanmax(v):.4g}")


if __name__ == "__main__":
    main()
