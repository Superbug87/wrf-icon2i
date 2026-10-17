#!/usr/bin/env python3
"""licenza_meteohub.py - legge da MeteoHub la licenza e l'attribuzione dei dataset ICON-2I (nessun dato personale in uscita)."""
import json
import os
import sys

import requests

BASE = "https://meteohub.agenziaitaliameteo.it"


def main():
    r = requests.post(f"{BASE}/auth/login", json={"username": os.environ["MH_EMAIL"], "password": os.environ["MH_PASSWORD"]}, timeout=60)
    j = r.json()
    h = {"Authorization": f"Bearer {j if isinstance(j, str) else j.get('token')}"}
    for u in ("/api/datasets", "/api/licenses", "/api/license", "/api/attributions"):
        x = requests.get(BASE + u, headers=h, timeout=60)
        print(f"== GET {u}: HTTP {x.status_code}")
        if x.status_code != 200:
            continue
        try:
            dati = x.json()
        except ValueError:
            print(x.text[:1500]); continue
        voci = dati if isinstance(dati, list) else dati.get("items", [dati])
        for v in voci:
            if not isinstance(v, dict):
                print(str(v)[:300]); continue
            if u == "/api/datasets" and "ICON" not in json.dumps(v).upper():
                continue
            print(json.dumps(v, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
