#!/usr/bin/env python3
"""licenza_meteohub.py - cerca nel sito MeteoHub il testo della pagina «Attribuzioni e licenze» (pagine e file pubblici)."""
import json
import re
import sys

import requests

BASE = "https://meteohub.agenziaitaliameteo.it"


def main():
    html = requests.get(f"{BASE}/app/license", timeout=60).text
    print("html", len(html), "byte")
    scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html)
    print("script:", scripts)
    for s in scripts:
        u = s if s.startswith("http") else BASE + (s if s.startswith("/") else "/app/" + s)
        js = requests.get(u, timeout=120).text
        print("==", u, len(js))
        for m in re.finditer(r"licen[sc]e", js, flags=re.I):
            a = max(0, m.start() - 150)
            print("   ...", js[a:m.end() + 250].replace("\n", " "))
            if m.start() > 0 and sum(1 for _ in re.finditer("", "")) > 0:
                break
        # file di testo/json citati vicino a "license"
        print("   percorsi json/md/html:", sorted(set(re.findall(r'["\'](/?[\w./-]*(?:licen|attribut|credit)[\w./-]*)["\']', js, flags=re.I)))[:30])
    for u in ("/app/assets/license.html", "/app/license.json", "/assets/license.md", "/api/info", "/api/status"):
        x = requests.get(BASE + u, timeout=60)
        print(f"GET {u}: HTTP {x.status_code} {x.headers.get('content-type')} {len(x.text)}")


if __name__ == "__main__":
    main()
