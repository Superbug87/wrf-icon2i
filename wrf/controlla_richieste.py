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
                    print("   voce completa:", json.dumps({k: x for k, x in v.items() if k != "args"})[:600])
                    nome = v.get("fileoutput") or v.get("filename") or v.get("output_file") or ""
                    prove = [f"/api/data/{nome}", f"/api/data/{v['id']}", f"/api/requests/{v['id']}/download",
                             f"/api/data/{v['id']}/download", f"/api/requests/{v['id']}"]
                    for u in prove:
                        r = requests.get(BASE + u, headers=h, timeout=300, stream=True)
                        print(f"   GET {u}: HTTP {r.status_code} {r.headers.get('content-type')} {r.headers.get('content-length')}")
                        if r.status_code == 200 and "json" not in (r.headers.get("content-type") or ""):
                            dati = r.content
                            (OUT / f"{v['name']}.grib").write_bytes(dati if len(dati) < 30e6 else dati[:30_000_000])
                            print(f"   scaricati {len(dati) / 1e6:.2f} MB, messaggi GRIB {dati.count(b'GRIB')}")
                            break
                        if r.status_code == 200:
                            print("   ", r.text[:300])
        if len(visti) == len(ids):
            break
        time.sleep(15)
    for v in lista:
        if v["id"] in ids and v["id"] not in visti:
            print(f"[{v['id']} {v['name']}] ancora {v['status']} dopo {time.time() - t0:.0f} s (inviata {v['submission_date']})")


if __name__ == "__main__":
    main()
