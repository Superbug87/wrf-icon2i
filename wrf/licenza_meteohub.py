#!/usr/bin/env python3
"""licenza_meteohub.py - licenza e attribuzione dei dataset ICON-2I secondo MeteoHub (nessun dato personale in uscita)."""
import json
import os

import requests

BASE = "https://meteohub.agenziaitaliameteo.it"


def main():
    r = requests.post(f"{BASE}/auth/login", json={"username": os.environ["MH_EMAIL"], "password": os.environ["MH_PASSWORD"]}, timeout=60)
    j = r.json()
    h = {"Authorization": f"Bearer {j if isinstance(j, str) else j.get('token')}"}
    for u in ("/api/datasets/ICON_2I_MODEL_LEVELS", "/api/datasets/ICON_2I_SURFACE_PRESSURE_LEVELS", "/api/all_licenses", "/api/licenses/all"):
        x = requests.get(BASE + u, headers=h, timeout=60)
        print(f"== GET {u}: HTTP {x.status_code}")
        if x.status_code == 200:
            try:
                print(json.dumps(x.json(), ensure_ascii=False, indent=1)[:4000])
            except ValueError:
                print(x.text[:2000])


if __name__ == "__main__":
    main()
