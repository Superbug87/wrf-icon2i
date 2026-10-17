#!/usr/bin/env python3
"""prova_icon2i.py - prova di scarica_icon2i.py senza rete: un finto MeteoHub risponde con GRIB2 costruiti al volo
(stessi codici, livelli e unità di quelli veri, griglia piu' rada) e si controlla il file che esce.

  python3 wrf/prova_icon2i.py
"""
import io
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

import eccodes as ec
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scarica_icon2i as s  # noqa: E402

s.TIPO_MOD = 100         # ecCodes non sa scrivere il tipo 150 senza coordinate verticali: nella prova i livelli del modello sono livelli di pressione
CICLO = datetime(2026, 10, 17, 12, tzinfo=timezone.utc)
LATS = np.arange(48.9, 33.65, -0.1)          # da nord a sud, come ICON-2I
LONS = np.arange(3.0, 22.05, 0.1)
NZ = 65
LAT2, LON2 = np.meshgrid(LATS, LONS, indexing="ij")
OROG = np.clip(600 * np.sin(np.radians(LON2 * 20)) * np.cos(np.radians(LAT2 * 15)) + 300, 0, 2500)   # m
OROG[LAT2 < 38] = 0.0                                                            # mare


def campo_base():
    h = ec.codes_grib_new_from_samples("regular_ll_sfc_grib2")
    ec.codes_set(h, "iDirectionIncrementInDegrees", 0.1)          # passo della griglia finta
    ec.codes_set(h, "jDirectionIncrementInDegrees", 0.1)
    return h


def msg(disc, cat, num, t1, v1, valori, lead=0, t2=None, v2=0, sc1=0, sc2=0):
    buf = io.BytesIO()
    s.scrivi(msg.base, buf, LATS, LONS, CICLO, lead, disc, cat, num, t1, v1, valori, tipo2=t2, sc2=sc2, v2=v2, sc1=sc1)
    return buf.getvalue()


msg.base = campo_base()


def atmosfera(lead):
    """Atmosfera sintetica: T = 288 - 6,5 K/km (min 216), p isoterma/politropica, vento crescente con la quota."""
    sigma = np.linspace(0.0, 1.0, NZ + 1)[1:]                     # 65 livelli dall'alto al basso
    zf = 20500.0 * (1 - sigma[:, None, None]) ** 1.3 + (OROG[None] + 10.0) * sigma[:, None, None] ** 3
    zf = np.maximum.accumulate(zf[::-1], axis=0)[::-1] if False else zf
    z = zf.astype("float64")
    T = np.maximum(288.15 - 0.0065 * z, 216.65)
    ps = 101325.0 * (1 - 0.0065 * (OROG + 10) / 288.15) ** 5.2559
    P = 101325.0 * (1 - 0.0065 * np.minimum(z, 11000) / 288.15) ** 5.2559
    P = np.where(z > 11000, 22632.0 * np.exp(-(z - 11000) / 6342.0), P)
    Q = 0.008 * np.exp(-z / 2500.0)
    U = 5.0 + z / 1000.0 + 0 * T
    V = -2.0 + 0 * T
    return z, T, P, Q, U, V, ps


def mod_gribs(lead, con_quota):
    z, T, P, Q, U, V, ps = atmosfera(lead)
    out = []
    for (cat, num, A) in ((0, 0, T), (1, 0, Q), (2, 2, U), (2, 3, V), (3, 0, P)) + (((3, 6, z),) if con_quota else ()):
        for k in range(NZ):
            out.append(msg(0, cat, num, s.TIPO_MOD, k + 1, A[k], lead, t2=s.TIPO_MOD, v2=k + 2))
    return b"".join(out)


def sup_gribs(ore):
    z, T, P, Q, U, V, ps = atmosfera(0)
    out = []
    for h in ore:
        t2 = T[-1] - 0.5
        for (disc, cat, num, t1, v1, val, kw) in (
                (0, 0, 0, 1, 0, T[-1] + 1, {}), (0, 0, 0, 103, 2, t2, {}), (0, 0, 6, 103, 2, t2 - 3, {}),
                (0, 1, 60, 1, 0, np.where(OROG > 1500, 40.0, 0.0), {}),
                (0, 2, 2, 103, 10, U[-1] * 0.5, {}), (0, 2, 3, 103, 10, V[-1], {}), (0, 3, 0, 1, 0, ps, {}),
                (0, 3, 1, 101, 0, 101325.0 + 0 * ps, {})):
            out.append(msg(disc, cat, num, t1, v1, val, h, **kw))
        for cm, (sc, v) in zip((0, 0.5, 2, 6, 18, 54, 162, 486, 1458), ((0, 0), (3, 5), (2, 2), (2, 6), (2, 18), (2, 54), (2, 162), (2, 486), (2, 1458))):
            out.append(msg(2, 3, 18, 106, v, T[-1] - 4 * (cm > 100), h, sc1=sc))
        for a, b in s.STRATI_ICON_CM:
            out.append(msg(2, 3, 20, 106, a, np.full(OROG.shape, 0.3 * (b - a) * 10.0), h, t2=106, v2=b, sc1=2, sc2=2))
    return b"".join(out)


class FintoHub:
    def __init__(self):
        self.chiamate = []

    def elenco(self, dataset):
        horas = range(0, 49, 6)
        tr = [{"desc": "Analysis or observation, istantaneous value"}] + [
            {"desc": f"Forecast at t+{60 * h} minute, instantaneous value"} for h in range(1, 49)]
        if dataset == s.MODELLO:
            prod = [{"desc": d} for d in ("Temperature (K)", "Specific humidity (kg/kg)", "u-component of wind (m/s)",
                                           "v-component of wind (m/s)", "Pressure (Pa)", "Geometric height (m)")]
            lev = [{"desc": f"150 ... {k}", "style": "GRIB2D", "l1": s.TIPO_MOD, "l2": s.TIPO_MOD, "value1": k, "value2": k + 1} for k in range(1, 66)]
            lev += [{"desc": f"150 ... {k}", "style": "GRIB2S", "level_type": 150, "value": k} for k in range(1, 67)]
            return {"product": prod, "level": lev, "timerange": tr}
        prod = [{"desc": d} for d in ("Temperature (K)", "Dewpoint temperature (K)", "u-component of wind (m/s)", "v-component of wind (m/s)",
                                       "Pressure (Pa)", "Pressure reduced to MSL (Pa)", "Snow depth water equivalent (kg m-2)",
                                       "Soil temperature (K)", "Column-integrated soil moisture (kg m-2)", "Land cover (1=land, 0=sea)")]
        return {"product": prod, "level": [{"desc": "sfc Ground or water surface 0 0"}, {"desc": "pl 850"}], "timerange": tr}

    def estrai(self, dataset, ciclo, filtri, nome, attesa=1200):
        self.chiamate.append(nome)
        if nome == "icon2i_lsm":
            return msg(2, 0, 0, 1, 0, (OROG > 0).astype(float))
        if nome.endswith("_sup"):
            ore = sorted({int(t["desc"].split("t+")[1].split(" ")[0]) // 60 if "t+" in t["desc"] else 0 for t in filtri["timerange"]})
            return sup_gribs(ore)
        lead = int(nome.split("_f")[1].split("_")[0])
        con_quota = any(p["desc"].startswith("Geometric") for p in filtri["product"])
        assert filtri["timerange"], "timerange vuoto"
        return mod_gribs(lead, con_quota)


def main():
    tmp = Path(tempfile.mkdtemp())
    s.Hub = FintoHub
    s.estrai_con_attesa = lambda hub, d, c, f, n, **k: hub.estrai(d, c, f, n)
    argv = ["scarica_icon2i.py", "--ciclo", "2026101712", "--ore", "12", "--passo", "6", "--out", str(tmp)]
    sys.argv = argv
    s.main()
    files = sorted(tmp.glob("*.grib2"))
    assert [f.name for f in files] == ["icon2i.t12z.f000.grib2", "icon2i.t12z.f006.grib2", "icon2i.t12z.f012.grib2"], files
    # contenuto del file: codici attesi dalla Vtable.ECMWF_OD
    chiavi, z850, t500 = {}, None, None
    with open(files[0], "rb") as f:
        while True:
            h = ec.codes_grib_new_from_file(f)
            if h is None:
                break
            g = lambda k: ec.codes_get_long(h, k)
            k = (g("discipline"), g("parameterCategory"), g("parameterNumber"), g("typeOfFirstFixedSurface"))
            chiavi.setdefault(k, 0)
            chiavi[k] += 1
            v = ec.codes_get_values(h).reshape(g("Nj"), g("Ni"))
            if k == (0, 3, 5, 100) and abs(g("scaledValueOfFirstFixedSurface") - 85000) < 1:
                z850 = v
            if k == (0, 0, 0, 100) and abs(g("scaledValueOfFirstFixedSurface") - 50000) < 1:
                t500 = v
            ec.codes_release(h)
    attesi = {(0, 0, 0, 100), (0, 2, 2, 100), (0, 2, 3, 100), (0, 1, 1, 100), (0, 3, 5, 100), (0, 2, 2, 103), (0, 2, 3, 103),
              (0, 0, 0, 103), (0, 0, 6, 103), (2, 0, 0, 1), (0, 3, 4, 1), (0, 3, 0, 1), (0, 3, 0, 101), (0, 0, 17, 1),
              (0, 1, 254, 1), (2, 3, 18, 106), (2, 0, 25, 106)}
    mancano = attesi - set(chiavi)
    assert not mancano, f"codici mancanti: {mancano}"
    assert chiavi[(0, 0, 0, 100)] >= 30, chiavi
    # atmosfera standard: a 850 hPa circa 1457 m e a 500 hPa circa 255,7 K (sul mare)
    assert 1400 < np.median(z850[LATS[:, None] < 37] if False else z850) < 1600, np.median(z850)
    assert 250 < np.median(t500) < 262, np.median(t500)
    print("prova_icon2i: tutto ok;", len(chiavi), "tipi di campo,", sum(chiavi.values()), "messaggi nel primo file")


if __name__ == "__main__":
    main()
