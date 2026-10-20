#!/usr/bin/env python3
"""
Construye el dataset comparativo Arkansas (05) vs Texas (48) a partir de
fuentes OFICIALES y SIN API KEY del U.S. Census Bureau:

  * Geometria de condados : TIGERweb Generalized_ACS2024/State_County (capa 12)
  * Poblacion 2000/2010/2020 : archivos estaticos de Population Estimates
      - 2000 : ESTIMATESBASE2000  (co-est00int-tot.csv)
      - 2010 : CENSUS2010POP      (co-est2020.csv)
      - 2020 : ESTIMATESBASE2020  (co-est2023-alldata.csv)

Salida (en web/data/):
  * compare.geojson     condados de AR+TX con pop/growth/centroide
  * compare_stats.json  agregados y series por estado
  * compare_quality.json reporte de calidad
  * compare_dictionary.json diccionario de datos
"""
import csv
import json
import os
import urllib.request
from shapely.geometry import shape, mapping

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "web", "data")
os.makedirs(RAW, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

STATES = {"05": "Arkansas", "48": "Texas"}
TOL = 0.006  # simplificacion (grados) - mayor para TX por volumen de condados

GEO_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "Generalized_ACS2024/State_County/MapServer/12/query"
    "?where=STATE%3D%2705%27%20OR%20STATE%3D%2748%27"
    "&outFields=GEOID,STATE,COUNTY,NAME,BASENAME"
    "&returnGeometry=true&f=geojson&outSR=4326"
)
POP_FILES = {
    "pop0010b.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2000-2010/intercensal/county/co-est00int-tot.csv",
    "pop1020.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/co-est2020.csv",
    "popest.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2023/counties/totals/co-est2023-alldata.csv",
}


def download(url, path, binary=True):
    if os.path.exists(path):
        return
    print("Descargando", os.path.basename(path), "...")
    with urllib.request.urlopen(url, timeout=180) as r:
        open(path, "wb").write(r.read())


def ensure_raw():
    download(GEO_URL, os.path.join(RAW, "census_counties_raw.json"))
    for fname, url in POP_FILES.items():
        download(url, os.path.join(RAW, fname))
    print("Fuentes listas.")


def load_pop():
    """Devuelve {geoid: {2000, 2010, 2020}} para AR y TX."""
    pop = {}

    def geoid(r):
        return r["STATE"].zfill(2) + r["COUNTY"].zfill(3)

    def want(r):
        # SUMLEV 50 = condado; puede venir como "50" o "050"
        return r.get("SUMLEV", "").lstrip("0") == "50" and r["STATE"].zfill(2) in STATES

    for r in csv.DictReader(open(os.path.join(RAW, "pop0010b.csv"), encoding="latin-1")):
        if want(r):
            pop.setdefault(geoid(r), {})["2000"] = int(r["ESTIMATESBASE2000"] or 0)
    for r in csv.DictReader(open(os.path.join(RAW, "pop1020.csv"), encoding="latin-1")):
        if want(r):
            pop.setdefault(geoid(r), {})["2010"] = int(r["CENSUS2010POP"] or 0)
    for r in csv.DictReader(open(os.path.join(RAW, "popest.csv"), encoding="latin-1")):
        if want(r):
            pop.setdefault(geoid(r), {})["2020"] = int(r["ESTIMATESBASE2020"] or 0)
    return pop


def round_coords(obj, nd=5):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(float(c), nd) for c in obj]
        return [round_coords(x, nd) for x in obj]
    return obj


def build():
    ensure_raw()
    geo = json.load(open(os.path.join(RAW, "census_counties_raw.json")))
    pop = load_pop()

    feats = []
    for f in geo["features"]:
        if not f.get("geometry"):
            continue
        p = f["properties"]
        gid = p["GEOID"]
        st = p["STATE"].zfill(2)
        pp = pop.get(gid, {})
        p2000 = pp.get("2000") or 0
        p2010 = pp.get("2010") or 0
        p2020 = pp.get("2020") or 0
        growth = round(((p2020 - p2000) / p2000) * 100, 1) if p2000 else 0

        geom = shape(f["geometry"])
        geom_s = geom.simplify(TOL, preserve_topology=True)
        if geom_s.is_empty:
            continue
        gj = mapping(geom_s)
        gj["coordinates"] = round_coords(gj["coordinates"])
        c = geom.centroid

        feats.append({
            "type": "Feature",
            "properties": {
                "geoid": gid,
                "state": st,
                "state_name": STATES[st],
                "name": p["BASENAME"],
                "pop2000": p2000,
                "pop2010": p2010,
                "pop2020": p2020,
                "growth": growth,
                "lon": round(c.x, 4),
                "lat": round(c.y, 4),
            },
            "geometry": gj,
        })

    fc = {"type": "FeatureCollection", "features": feats}
    path = os.path.join(OUT, "compare.geojson")
    json.dump(fc, open(path, "w"), separators=(",", ":"))
    print(f"compare.geojson: {len(feats)} condados, {os.path.getsize(path)/1024:.0f} KB")

    # ---- estadisticas por estado ----
    stats = {"generated_from": "U.S. Census Bureau (TIGERweb + Population Estimates)",
             "crs": "EPSG:4326 (WGS 84)", "states": {}}
    for st, name in STATES.items():
        sf = [f for f in feats if f["properties"]["state"] == st]
        tot = {y: sum(f["properties"][f"pop{y}"] for f in sf) for y in (2000, 2010, 2020)}
        top = sorted(sf, key=lambda f: f["properties"]["pop2020"], reverse=True)[:5]
        fastest = sorted(sf, key=lambda f: f["properties"]["growth"], reverse=True)[:5]
        stats["states"][st] = {
            "name": name,
            "counties": len(sf),
            "pop": tot,
            "growth_2000_2020": round((tot[2020] - tot[2000]) / tot[2000] * 100, 1),
            "top_pop": [{"name": f["properties"]["name"], "pop": f["properties"]["pop2020"]} for f in top],
            "fastest": [{"name": f["properties"]["name"], "growth": f["properties"]["growth"]} for f in fastest],
        }
    json.dump(stats, open(os.path.join(OUT, "compare_stats.json"), "w"), indent=2)
    print("compare_stats.json escrito")

    # ---- diccionario de datos ----
    dic = {
        "label": "Condados (AR vs TX)",
        "fields": [
            {"field": "geoid", "type": "codigo", "desc": "GEOID del condado (STATE+COUNTY)", "unit": ""},
            {"field": "state_name", "type": "texto", "desc": "Estado (Arkansas o Texas)", "unit": ""},
            {"field": "name", "type": "texto", "desc": "Nombre del condado", "unit": ""},
            {"field": "pop2000 / pop2010 / pop2020", "type": "numero", "desc": "Poblacion censal decenal", "unit": "habitantes"},
            {"field": "growth", "type": "numero", "desc": "Crecimiento poblacional 2000→2020", "unit": "%"},
            {"field": "lat / lon", "type": "numero", "desc": "Centroide geometrico", "unit": "grados (EPSG:4326)"},
        ],
    }
    json.dump(dic, open(os.path.join(OUT, "compare_dictionary.json"), "w"), indent=2)
    print("compare_dictionary.json escrito")

    # ---- calidad de datos ----
    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    def quality(sf, name):
        total = len(sf)
        rep = {"records": total, "fields": {}, "issues": []}
        for field in ("pop2000", "pop2010", "pop2020", "growth"):
            vals = [num(f["properties"].get(field)) for f in sf]
            present = sum(1 for v in vals if v != 0)
            zeros = sum(1 for v in vals if v == 0)
            rep["fields"][field] = {
                "completeness": round(present / total * 100, 1) if total else 0,
                "zeros": zeros, "min": min(vals), "max": max(vals),
                "mean": round(sum(vals) / len(vals), 1),
            }
        gids = [f["properties"]["geoid"] for f in sf]
        dups = total - len(set(gids))
        if dups:
            rep["issues"].append(f"{dups} GEOID duplicado(s)")
        neg = sum(1 for f in sf if f["properties"]["growth"] < 0)
        rep["issues"].append(f"{neg} condado(s) con crecimiento negativo (despoblacion)")
        return rep

    q = {"generated_from": "U.S. Census Bureau", "crs": "EPSG:4326 (WGS 84)",
         "states": {st: quality([f for f in feats if f["properties"]["state"] == st], STATES[st])
                    for st in STATES}}
    json.dump(q, open(os.path.join(OUT, "compare_quality.json"), "w"), indent=2)
    print("compare_quality.json escrito")
    print("Listo.")


if __name__ == "__main__":
    build()
