#!/usr/bin/env python3
"""controlla_richieste.py - elenco delle richieste fatte a MeteoHub con l'account: stato, tempi, e scarico di quelle finite."""
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prova_estrazione import BASE, OUT, login, scarica  # noqa: E402


def main():
    OUT.mkdir(exist_ok=True)
    h = {"Authorization": f"Bearer {login()}"}
    ids = {int(x) for x in os.environ.get("RICHIESTE", "").split(",") if x.strip()}
    t0 = time.time()
    visti = {}
    while time.time() - t0 < 900:
        lista = requests.get(f"{BASE}/api/requests", headers=h, timeout=60).json()
        for v in lista:
            if v["id"] in ids and v["status"] not in ("PENDING", "STARTED", "PROGRESS") and v["id"] not in visti:
                visti[v["id"]] = v
                print(f"[{v['id']} {v['name']}] {v['status']} inviata {v['submission_date']} finita {v.get('end_date')} "
                      f"{v.get('error_message', '')} filesize={v.get('filesize')} filename={v.get('filename')}")
                if v["status"] == "SUCCESS":
                    scarica(h, v["name"], v)
        if len(visti) == len(ids):
            break
        time.sleep(15)
    for v in lista:
        if v["id"] in ids and v["id"] not in visti:
            print(f"[{v['id']} {v['name']}] ancora {v['status']} dopo {time.time() - t0:.0f} s (inviata {v['submission_date']})")


if __name__ == "__main__":
    main()
