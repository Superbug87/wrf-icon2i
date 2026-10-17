#!/usr/bin/env python3
"""
scopri_meteohub.py - entra in MeteoHub (Agenzia ItaliaMeteo) con l'account e scrive cosa offre ICON-2I:
quali campi (variabile, livello, tipo di tempo) ci sono nei dataset di superficie/pressione e sui livelli del modello.
Serve a decidere se ICON-2I basta per far partire WRF (servono T, vento, umidità, quota geopotenziale in quota,
pressione al suolo, suolo e mare). Non scrive mai le credenziali.

Segreti (variabili d'ambiente): MH_EMAIL, MH_PASSWORD.
Uscita: cartella `scoperta/` con i JSON grezzi e `riassunto.txt`.
"""
import json
import os
import sys
from pathlib import Path

import requests

BASE = "https://meteohub.agenziaitaliameteo.it"
DATASET = ["ICON_2I_SURFACE_PRESSURE_LEVELS", "ICON_2I_MODEL_LEVELS"]
OUT = Path("scoperta")


def login():
    email, pw = os.environ.get("MH_EMAIL", ""), os.environ.get("MH_PASSWORD", "")
    if not email or not pw:
        sys.exit("Mancano i segreti MH_EMAIL e MH_PASSWORD.")
    r = requests.post(f"{BASE}/auth/login", json={"username": email, "password": pw}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"Login rifiutato (HTTP {r.status_code}): {r.text[:200].replace(pw, '***')}")
    j = r.json()
    tok = j if isinstance(j, str) else (j.get("token") or j.get("Response", {}).get("data", {}).get("token") if isinstance(j, dict) else None)
    if not tok:
        sys.exit("Login riuscito ma non trovo il token nella risposta (chiavi: %s)" % (list(j) if isinstance(j, dict) else type(j)))
    print("login ok")
    return tok


def main():
    OUT.mkdir(exist_ok=True)
    tok = login()
    h = {"Authorization": f"Bearer {tok}"}
    righe = []
    for d in DATASET:
        r = requests.get(f"{BASE}/api/fields", params={"datasets": d}, headers=h, timeout=120)
        righe.append(f"== {d}: HTTP {r.status_code}, {len(r.content)} byte")
        (OUT / f"fields_{d}.json").write_bytes(r.content)
        if r.status_code != 200:
            righe.append(r.text[:300])
            continue
        j = r.json()
        if isinstance(j, dict):
            righe.append("chiavi: " + ", ".join(f"{k}({type(v).__name__})" for k, v in j.items()))
            for k, v in j.items():
                if isinstance(v, (list, dict)):
                    righe.append(f"  {k}: " + json.dumps(v, ensure_ascii=False)[:1500])
        else:
            righe.append(json.dumps(j, ensure_ascii=False)[:1500])
        # risposta di sintesi (valori distinti per ogni filtro)
        r2 = requests.get(f"{BASE}/api/datasets/{d}", headers=h, timeout=60)
        righe.append(f"  dettaglio dataset: HTTP {r2.status_code} " + r2.text[:600])
    (OUT / "riassunto.txt").write_text("\n".join(righe), encoding="utf-8")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
