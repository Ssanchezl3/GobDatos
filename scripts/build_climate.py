#!/usr/bin/env python3
"""
INGESTA F03 — Clima de Arkansas (NOAA NCEI U.S. Climate Normals 1991-2020)

Fuente oficial, dominio publico, SIN API KEY:
  https://www.ncei.noaa.gov/data/normals-monthly/1991-2020/

Proceso:
  1. Descarga el inventario de estaciones (fixed-width) y filtra Arkansas (AR).
  2. Para cada estacion AR descarga sus normales mensuales (12 filas).
  3. Calcula promedios anuales de temperatura y precipitacion por estacion.
  4. Produce web/data/climate.geojson (puntos) con trazabilidad a F03.

Para no saturar el servidor se limita el numero de estaciones (MAX_STATIONS),
priorizando las que tienen datos de temperatura completos.
"""
import csv
import io
import json
import os
import time
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "web", "data")
os.makedirs(RAW, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

BASE = "https://www.ncei.noaa.gov/data/normals-monthly/1991-2020"
INV_URL = f"{BASE}/doc/inventory_30yr.txt"
ACCESS = f"{BASE}/access"
MAX_STATIONS = 90  # cota razonable para una ingesta reproducible


def download(url, path):
    if os.path.exists(path):
        return
    with urllib.request.urlopen(url, timeout=120) as r:
        open(path, "wb").write(r.read())


def ar_stations():
    """Lee el inventario fixed-width y devuelve estaciones de Arkansas."""
    download(INV_URL, os.path.join(RAW, "noaa_inventory.txt"))
    out = []
    for line in open(os.path.join(RAW, "noaa_inventory.txt"), encoding="latin-1"):
        parts = line.split()
        if len(parts) < 6:
            continue
        sid, slat, slon, selev, state = parts[0], parts[1], parts[2], parts[3], parts[4]
        if state != "AR":
            continue
        try:
            lat = float(slat); lon = float(slon); elev = float(selev)
        except ValueError:
            continue
        name = " ".join(parts[5:])
        out.append({"id": sid, "lat": lat, "lon": lon, "elev": elev, "name": name})
    return out


def fnum(v):
    try:
        f = float(v)
        return None if f <= -9999 else f
    except (TypeError, ValueError):
        return None


def station_normals(sid):
    """Descarga normales mensuales y promedia a valores anuales."""
    url = f"{ACCESS}/{sid}.csv"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            text = r.read().decode("latin-1")
    except Exception:
        return None
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return None
    tavg = [fnum(r.get("MLY-TAVG-NORMAL")) for r in rows]
    tmax = [fnum(r.get("MLY-TMAX-NORMAL")) for r in rows]
    tmin = [fnum(r.get("MLY-TMIN-NORMAL")) for r in rows]
    prcp = [fnum(r.get("MLY-PRCP-NORMAL")) for r in rows]
    tavg = [v for v in tavg if v is not None]
    tmax = [v for v in tmax if v is not None]
    tmin = [v for v in tmin if v is not None]
    prcp = [v for v in prcp if v is not None]
    if len(tavg) < 12:
        return None
    return {
        "tavg_annual": round(sum(tavg) / len(tavg), 1),          # °F
        "tmax_annual": round(sum(tmax) / len(tmax), 1) if tmax else None,
        "tmin_annual": round(sum(tmin) / len(tmin), 1) if tmin else None,
        "prcp_annual": round(sum(prcp), 2) if len(prcp) >= 12 else None,  # pulgadas/año
        "tavg_by_month": [round(v, 1) for v in tavg[:12]],
    }


def build():
    stations = ar_stations()
    print(f"Estaciones AR en inventario: {len(stations)}")
    # priorizar estaciones tipo aeropuerto/COOP (USW/USC) con mejor cobertura
    stations.sort(key=lambda s: (0 if s["id"].startswith(("USW", "USC")) else 1))
    feats = []
    tested = 0
    for s in stations:
        if len(feats) >= MAX_STATIONS:
            break
        tested += 1
        norm = station_normals(s["id"])
        if not norm:
            continue
        props = {"station_id": s["id"], "name": s["name"],
                 "elev_ft": s["elev"], **norm}
        feats.append({
            "type": "Feature",
            "properties": props,
            "geometry": {"type": "Point", "coordinates": [round(s["lon"], 4), round(s["lat"], 4)]},
        })
        time.sleep(0.05)
    fc = {"type": "FeatureCollection", "features": feats}
    path = os.path.join(OUT, "climate.geojson")
    json.dump(fc, open(path, "w"), separators=(",", ":"))
    print(f"climate.geojson: {len(feats)} estaciones (de {tested} probadas), "
          f"{os.path.getsize(path)/1024:.0f} KB")

    _merge_dictionary_quality(feats)
    return fc


def _merge_dictionary_quality(feats):
    """Añade la capa 'climate' a dictionary.json y quality.json del lago."""
    # --- diccionario ---
    dic_path = os.path.join(OUT, "dictionary.json")
    dic = json.load(open(dic_path, encoding="utf-8")) if os.path.exists(dic_path) else {}
    dic["climate"] = {
        "label": "Clima — estaciones NOAA (F03)",
        "fields": [
            {"field": "station_id", "type": "codigo", "desc": "Identificador de estación NOAA", "unit": ""},
            {"field": "name", "type": "texto", "desc": "Nombre de la estación", "unit": ""},
            {"field": "elev_ft", "type": "numero", "desc": "Elevación", "unit": "pies"},
            {"field": "tavg_annual", "type": "numero", "desc": "Temperatura media anual", "unit": "°F"},
            {"field": "tmax_annual", "type": "numero", "desc": "Temperatura máxima media anual", "unit": "°F"},
            {"field": "tmin_annual", "type": "numero", "desc": "Temperatura mínima media anual", "unit": "°F"},
            {"field": "prcp_annual", "type": "numero", "desc": "Precipitación anual", "unit": "pulgadas"},
        ],
    }
    json.dump(dic, open(dic_path, "w"), ensure_ascii=False, indent=2)

    # --- calidad ---
    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    q_path = os.path.join(OUT, "quality.json")
    q = json.load(open(q_path, encoding="utf-8")) if os.path.exists(q_path) else {}
    total = len(feats)
    fields = {}
    for field in ("tavg_annual", "tmax_annual", "tmin_annual", "prcp_annual", "elev_ft"):
        vals = [f["properties"].get(field) for f in feats]
        present = sum(1 for v in vals if v not in (None, ""))
        nums = [num(v) for v in vals if v not in (None, "")]
        rec = {"completeness": round(present / total * 100, 1) if total else 0,
               "nulls": total - present}
        if nums:
            rec["min"] = min(nums); rec["max"] = max(nums)
            rec["mean"] = round(sum(nums) / len(nums), 1)
        fields[field] = rec
    ids = [f["properties"]["station_id"] for f in feats]
    dups = total - len(set(ids))
    q["climate"] = {
        "records": total, "fields": fields, "key_field": "station_id",
        "unique_keys": len(set(ids)),
        "issues": [f"{dups} station_id duplicado(s)"] if dups else ["Sin anomalias detectadas"],
    }
    json.dump(q, open(q_path, "w"), ensure_ascii=False, indent=2)
    print("dictionary.json y quality.json actualizados con la capa 'climate'")


if __name__ == "__main__":
    build()
