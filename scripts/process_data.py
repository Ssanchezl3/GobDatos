#!/usr/bin/env python3
"""
Procesa y simplifica los GeoJSON crudos descargados del portal oficial de
Arkansas GIS (https://geodata.gis.arkansas.gov/) para producir archivos
compactos y limpios listos para la visualizacion web.

Fuente: Arkansas GIS Office - FEATURESERVICES/Boundaries (FeatureServer)
"""
import json
import os
from shapely.geometry import shape, mapping

RAW = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(os.path.dirname(__file__), "..", "web", "data")
os.makedirs(OUT, exist_ok=True)

# Tolerancia de simplificacion en grados (~ aprox). Mayor = mas liviano.
TOL = 0.0015


def round_coords(obj, nd=5):
    """Redondea coordenadas para reducir tamano del archivo."""
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(float(c), nd) for c in obj]
        return [round_coords(x, nd) for x in obj]
    return obj


def simplify_feature(feat, keep_props, tol=TOL):
    geom = shape(feat["geometry"])
    geom = geom.simplify(tol, preserve_topology=True)
    if geom.is_empty:
        return None
    gj = mapping(geom)
    gj["coordinates"] = round_coords(gj["coordinates"])
    props = {}
    src = feat["properties"]
    for k, out in keep_props.items():
        props[out] = src.get(k)
    return {"type": "Feature", "properties": props, "geometry": gj}


def process(infile, outfile, keep_props, tol=TOL):
    data = json.load(open(os.path.join(RAW, infile)))
    out_feats = []
    for f in data["features"]:
        if not f.get("geometry"):
            continue
        sf = simplify_feature(f, keep_props, tol)
        if sf:
            out_feats.append(sf)
    fc = {"type": "FeatureCollection", "features": out_feats}
    path = os.path.join(OUT, outfile)
    json.dump(fc, open(path, "w"), separators=(",", ":"))
    size = os.path.getsize(path) / 1024
    print(f"{outfile}: {len(out_feats)} features, {size:.0f} KB")
    return fc


# ---- Condados: poblacion decadal 1900-2020 ----
county_props = {
    "county": "name",
    "countyfips": "fips",
    "sq_miles": "sq_miles",
}
for yr in [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]:
    county_props[f"pop{yr}"] = f"pop{yr}"
counties = process("counties_raw.json", "counties.geojson", county_props, tol=0.004)

# ---- Municipios ----
muni_props = {
    "city_name": "name",
    "city_fips": "fips",
    "classification": "classification",
    "squaremiles": "sq_miles",
    "pop2000": "pop2000",
    "pop2010": "pop2010",
    "pop2020": "pop2020",
}
munis = process("municipalities_raw.json", "municipalities.geojson", muni_props, tol=0.002)

# ---- Distritos congresionales ----
cong_props = {"district": "district"}
cong = process("congress_raw.json", "congress.geojson", cong_props, tol=0.004)

# ---- Estadisticas agregadas para el dashboard ----
def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

stats = {
    "generated_from": "Arkansas GIS Office - geodata.gis.arkansas.gov",
    "counties": {
        "count": len(counties["features"]),
        "total_pop2020": int(sum(num(f["properties"]["pop2020"]) for f in counties["features"])),
        "total_sq_miles": round(sum(num(f["properties"]["sq_miles"]) for f in counties["features"]), 1),
    },
    "municipalities": {
        "count": len(munis["features"]),
        "by_class": {},
        "total_pop2020": int(sum(num(f["properties"]["pop2020"]) for f in munis["features"])),
    },
    "congress_districts": len(cong["features"]),
}
for f in munis["features"]:
    c = f["properties"].get("classification") or "Unknown"
    stats["municipalities"]["by_class"][c] = stats["municipalities"]["by_class"].get(c, 0) + 1

# serie de poblacion estatal por decada
decades = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
stats["state_pop_series"] = [
    {"year": y, "pop": int(sum(num(f["properties"].get(f"pop{y}")) for f in counties["features"]))}
    for y in decades
]

json.dump(stats, open(os.path.join(OUT, "stats.json"), "w"), indent=2)
print("stats.json written")
print("Done.")
