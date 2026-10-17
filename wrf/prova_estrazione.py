#!/usr/bin/env python3
"""
prova_estrazione.py - prova l'estrazione dati di MeteoHub (POST /api/data) con l'account: richiesta, attesa, scarico,
peso del file, con e senza ritaglio dell'area. Segreti: MH_EMAIL, MH_PASSWORD (mai scritti nel log).
Uscita: cartella `scoperta/` (file GRIB di prova, piccoli).
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = "https://meteohub.agenziaitaliameteo.it"
OUT = Path("scoperta")


def login():
    r = requests.post(f"{BASE}/auth/login", json={"username": os.environ["MH_EMAIL"], "password": os.environ["MH_PASSWORD"]}, timeout=60)
    r.raise_for_status()
    j = r.json()
    return j if isinstance(j, str) else j.get("token")


def estrai(h, nome, corpo, attesa=600):
    t0 = time.time()
    r = requests.post(f"{BASE}/api/data", json=corpo, headers=h, timeout=120)
    print(f"[{nome}] POST HTTP {r.status_code} {r.text[:300]}")
    if r.status_code != 202:
        return None
    rid = r.json()["request_id"]
    while time.time() - t0 < attesa:
        time.sleep(5)
        lista = requests.get(f"{BASE}/api/requests", headers=h, timeout=60).json()
        v = next((x for x in lista if x["id"] == rid), None)
        if v and v["status"] not in ("PENDING", "STARTED", "PROGRESS"):
            print(f"[{nome}] stato {v['status']} dopo {time.time() - t0:.0f} s; chiavi: {sorted(k for k in v if k != 'args')}")
            print(f"[{nome}]", json.dumps({k: v[k] for k in v if k != "args"})[:600])
            return v
    print(f"[{nome}] ancora in corso dopo {attesa} s")
    return None


def scarica(h, nome, v):
    fn = v.get("filename")
    if not fn:
        return
    for url in (f"{BASE}/api/data/{fn}", f"{BASE}/api/data/{v['id']}", f"{BASE}/api/requests/{v['id']}/download"):
        r = requests.get(url, headers=h, timeout=300, stream=True)
        print(f"[{nome}] GET {url.replace(BASE, '')}: HTTP {r.status_code} {r.headers.get('content-type')} {r.headers.get('content-length')}")
        if r.status_code == 200:
            dati = r.content
            (OUT / f"{nome}.grib").write_bytes(dati)
            print(f"[{nome}] scaricati {len(dati) / 1e6:.2f} MB, messaggi GRIB: {dati.count(b'GRIB')}")
            return


def main():
    OUT.mkdir(exist_ok=True)
    h = {"Authorization": f"Bearer {login()}"}
    j = requests.get(f"{BASE}/api/fields", params={"datasets": "ICON_2I_MODEL_LEVELS"}, headers=h, timeout=120).json()["items"]
    prod = [p for p in j["product"] if p["desc"].startswith(("Temperature", "Pressure (Pa)"))]
    liv = j["level"][:2]
    f = "%Y-%m-%dT%H:%M:%S.000Z"
    run = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)          # l'ultimo ciclo elencato da /api/fields
    temp = [prod[0]]
    sp = requests.get(f"{BASE}/api/fields", params={"datasets": "ICON_2I_SURFACE_PRESSURE_LEVELS"}, headers=h, timeout=120).json()["items"]
    t2 = [p for p in sp["product"] if p["desc"] == "Temperature (K)"]
    l2 = [l for l in sp["level"] if l["desc"].endswith(" h2") or l["desc"].endswith("(m) 0 2")]
    print("livello 2 m:", l2[:1], " | prodotto T:", t2[:1])
    ven = lambda dt: {"from": dt.strftime(f), "to": dt.strftime(f)}
    prove = {
        "E_superficie_T2m": ({"reftime": ven(run)}, {}, "ICON_2I_SURFACE_PRESSURE_LEVELS", {"product": t2, "level": l2[:1]}),
        "F_livelli_solo_livello1": ({"reftime": ven(run)}, {}, "ICON_2I_MODEL_LEVELS", {"level": liv[:1]}),
        "G_modello_T_livello1_senza_run": ({"reftime": ven(run)}, {}, "ICON_2I_MODEL_LEVELS", {"product": temp, "level": liv[:1]}),
        "H_ritaglio": ({"reftime": ven(run)}, {"postprocessors": [{"sub_type": "bbox", "processor_type": "grid_cropping",
                       "boundings": {"ilon": 6.5, "ilat": 37.0, "flon": 19.0, "flat": 46.5}}]},
                       "ICON_2I_SURFACE_PRESSURE_LEVELS", {"product": t2, "level": l2[:1]}),
    }
    for nome, (parte, extra, dset, filtri) in prove.items():
        corpo = {"request_name": nome, "dataset_names": [dset], "only_reliable": False, **parte, "filters": filtri, **extra}
        v = estrai(h, nome, corpo, attesa=180)
        if v and v["status"] == "SUCCESS":
            scarica(h, nome, v)


if __name__ == "__main__":
    main()
