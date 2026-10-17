#!/usr/bin/env python3
"""
prova_estrazione.py - sonda l'API di estrazione dati di MeteoHub (POST /api/data) con l'account, per scoprire i campi
richiesti dalla richiesta (gli errori di validazione li elencano) e, se la richiesta e' valida, quanto pesa e quanto ci mette.
Segreti: MH_EMAIL, MH_PASSWORD. Non scrive mai le credenziali.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://meteohub.agenziaitaliameteo.it"


def login():
    email, pw = os.environ["MH_EMAIL"], os.environ["MH_PASSWORD"]
    r = requests.post(f"{BASE}/auth/login", json={"username": email, "password": pw}, timeout=60)
    r.raise_for_status()
    j = r.json()
    return j if isinstance(j, str) else j.get("token")


def mostra(titolo, r):
    print(f"--- {titolo}: HTTP {r.status_code}\n{r.text[:1500]}\n")


def main():
    h = {"Authorization": f"Bearer {login()}"}
    mostra("POST /api/data {} (cerco i campi richiesti)", requests.post(f"{BASE}/api/data", json={}, headers=h, timeout=60))
    run = (datetime.now(timezone.utc) - timedelta(hours=14)).replace(hour=0, minute=0, second=0, microsecond=0)
    for _ in range(2):
        ok = requests.get(f"{BASE}/api/datasets/ICON_2I_MODEL_LEVELS/opendata", headers=h, timeout=60)
        break
    j = requests.get(f"{BASE}/api/fields", params={"datasets": "ICON_2I_MODEL_LEVELS"}, headers=h, timeout=120).json()["items"]
    prod = [p for p in j["product"] if p["desc"].startswith(("Temperature", "Pressure (Pa)"))]
    liv = j["level"][:2]
    tr = [t for t in j["timerange"] if t["desc"].startswith("Forecast at t+60 ")]
    corpo = {
        "request_name": "prova",
        "reftime": {"from": run.strftime("%Y-%m-%dT%H:%M:%S.000Z"), "to": run.strftime("%Y-%m-%dT%H:%M:%S.000Z")},
        "dataset_names": ["ICON_2I_MODEL_LEVELS"],
        "filters": {"product": prod, "level": liv, "timerange": tr, "run": [r for r in j["run"] if r["value"] == 0]},
        "output_format": "grib",
        "only_reliable": False,
    }
    print("corpo di prova:", json.dumps(corpo, ensure_ascii=False)[:1200])
    r = requests.post(f"{BASE}/api/data", json=corpo, headers=h, timeout=120)
    mostra("POST /api/data (richiesta di prova piccola)", r)
    if r.status_code in (200, 202):
        rid = r.json().get("request_id") or r.json().get("id")
        print("richiesta:", rid)
        for _ in range(30):
            time.sleep(10)
            for url in (f"{BASE}/api/requests/{rid}", f"{BASE}/api/requests"):
                s = requests.get(url, headers=h, timeout=60)
                mostra(f"GET {url}", s)
            break


if __name__ == "__main__":
    main()
