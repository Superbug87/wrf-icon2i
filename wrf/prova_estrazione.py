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
    """Misura: tutta la temperatura sui livelli del modello per due istanti (tempo in coda, peso, velocita' di scarico)."""
    OUT.mkdir(exist_ok=True)
    h = {"Authorization": f"Bearer {login()}"}
    j = requests.get(f"{BASE}/api/fields", params={"datasets": "ICON_2I_MODEL_LEVELS"}, headers=h, timeout=120).json()["items"]
    temp = [p for p in j["product"] if p["desc"].startswith("Temperature")]
    tr = [t for t in j["timerange"] if t["desc"] in ("Forecast at t+0 minute, instantaneous value", "Analysis or observation, istantaneous value",
                                                    "Forecast at t+180 minute, instantaneous value")]
    print("timerange usati:", [t["desc"] for t in tr], "| livelli:", len(j["level"]))
    f = "%Y-%m-%dT%H:%M:%S.000Z"
    run = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
    corpo = {"request_name": "misura_T_tutti_livelli", "dataset_names": ["ICON_2I_MODEL_LEVELS"], "only_reliable": False,
             "reftime": {"from": run.strftime(f), "to": run.strftime(f)}, "filters": {"product": temp, "timerange": tr}}
    t0 = time.time()
    v = estrai(h, "misura", corpo, attesa=1500)
    if v and v["status"] == "SUCCESS":
        t1 = time.time()
        r = requests.get(f"{BASE}/api/data/{v['fileoutput']}", headers=h, timeout=900, stream=True)
        n = 0
        dati = bytearray()
        for blocco in r.iter_content(1 << 20):
            n += len(blocco)
            dati += blocco
        # i primi 12 messaggi e gli ultimi 3, per guardarli: struttura, livelli, griglia
        pos = [i for i in range(len(dati) - 4) if dati[i:i + 4] == b"GRIB"]
        pos.append(len(dati))
        (OUT / "campione_T.grib").write_bytes(bytes(dati[pos[0]:pos[12]]) + bytes(dati[pos[-4]:pos[-1]]))
        print(f"[misura] messaggi: {len(pos) - 1}")
        dt = time.time() - t1
        print(f"[misura] coda+calcolo {t1 - t0:.0f} s; scarico {n / 1e6:.1f} MB in {dt:.0f} s = {n / 1e6 / max(dt, 1e-3):.1f} MB/s")


if __name__ == "__main__":
    main()
