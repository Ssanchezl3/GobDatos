#!/usr/bin/env python3
"""
Procesa y simplifica los GeoJSON crudos descargados del portal oficial de
Arkansas GIS (https://geodata.gis.arkansas.gov/) para producir archivos
compactos y limpios listos para la visualizacion web.

Fuente: Arkansas GIS Office - FEATURESERVICES/Boundaries (FeatureServer)

Si los GeoJSON crudos no existen en ./data, se descargan automaticamente
desde el servicio ArcGIS REST oficial (requiere conexion a internet).
"""
import json
import os
import urllib.request
from shapely.geometry import shape, mapping

RAW = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(os.path.dirname(__file__), "..", "web", "data")
os.makedirs(OUT, exist_ok=True)
os.makedirs(RAW, exist_ok=True)

# Endpoint oficial ArcGIS REST - capas del FeatureServer de limites
BASE = "https://gis.arkansas.gov/arcgis/rest/services/FEATURESERVICES/Boundaries/FeatureServer"
LAYERS = {  # archivo crudo -> id de capa en el FeatureServer
    "counties_raw.json": 48,       # COUNTY_BOUNDARY
    "municipalities_raw.json": 41, # MUNICIPAL_BOUNDARY
    "congress_raw.json": 6,        # CONGRESSIONAL_DISTRICTS
}


def ensure_raw():
    """Descarga los GeoJSON crudos desde ArcGIS REST si no estan en disco."""
    for fname, layer_id in LAYERS.items():
        path = os.path.join(RAW, fname)
        if os.path.exists(path):
            continue
        url = (f"{BASE}/{layer_id}/query?where=1%3D1&outFields=*"
               f"&f=geojson&outSR=4326")
        print(f"Descargando {fname} (capa {layer_id}) ...")
        with urllib.request.urlopen(url, timeout=120) as r:
            open(path, "wb").write(r.read())
    print("Datos crudos listos.")

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
    geom_s = geom.simplify(tol, preserve_topology=True)
    if geom_s.is_empty:
        return None
    gj = mapping(geom_s)
    gj["coordinates"] = round_coords(gj["coordinates"])
    props = {}
    src = feat["properties"]
    for k, out in keep_props.items():
        props[out] = src.get(k)
    # centroide (para burbujas proporcionales) calculado del poligono original
    try:
        c = geom.centroid
        props["_lon"] = round(c.x, 4)
        props["_lat"] = round(c.y, 4)
    except Exception:
        pass
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


ensure_raw()

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


# ============================================================
#  GOBERNANZA: Diccionario de datos + Reporte de calidad
# ============================================================

# ---- Diccionario de datos (metadatos por campo) ----
data_dictionary = {
    "counties": {
        "label": "Condados",
        "fields": [
            {"field": "name", "type": "texto", "desc": "Nombre del condado", "unit": ""},
            {"field": "fips", "type": "codigo", "desc": "Codigo FIPS del condado (3 digitos)", "unit": ""},
            {"field": "sq_miles", "type": "numero", "desc": "Superficie del condado", "unit": "millas cuadradas"},
            {"field": "pop1900..pop2020", "type": "numero", "desc": "Poblacion censal por decada (13 censos)", "unit": "habitantes"},
            {"field": "_lat / _lon", "type": "numero", "desc": "Centroide geometrico (derivado)", "unit": "grados (EPSG:4326)"},
        ],
    },
    "municipalities": {
        "label": "Municipios",
        "fields": [
            {"field": "name", "type": "texto", "desc": "Nombre de la ciudad", "unit": ""},
            {"field": "fips", "type": "codigo", "desc": "Codigo FIPS de la ciudad", "unit": ""},
            {"field": "classification", "type": "categoria", "desc": "Clase legal municipal (Primera/Segunda/Incorporado)", "unit": ""},
            {"field": "sq_miles", "type": "numero", "desc": "Superficie del municipio", "unit": "millas cuadradas"},
            {"field": "pop2000 / pop2010 / pop2020", "type": "numero", "desc": "Poblacion censal", "unit": "habitantes"},
            {"field": "_lat / _lon", "type": "numero", "desc": "Centroide geometrico (derivado)", "unit": "grados (EPSG:4326)"},
        ],
    },
    "congress": {
        "label": "Distritos Congresionales",
        "fields": [
            {"field": "district", "type": "codigo", "desc": "Numero del distrito federal", "unit": ""},
            {"field": "_lat / _lon", "type": "numero", "desc": "Centroide geometrico (derivado)", "unit": "grados (EPSG:4326)"},
        ],
    },
}
json.dump(data_dictionary, open(os.path.join(OUT, "dictionary.json"), "w"), indent=2)
print("dictionary.json written")


# ---- Reporte de calidad de datos ----
def quality_for(features, numeric_fields, key_field):
    total = len(features)
    report = {"records": total, "fields": {}, "issues": []}
    # completitud por campo
    all_fields = set()
    for f in features:
        all_fields.update(f["properties"].keys())
    all_fields = [c for c in all_fields if not c.startswith("_")]
    for field in sorted(all_fields):
        present = sum(1 for f in features
                      if f["properties"].get(field) not in (None, "", " "))
        nulls = total - present
        rec = {
            "completeness": round(present / total * 100, 1) if total else 0,
            "nulls": nulls,
        }
        if field in numeric_fields:
            vals = [num(f["properties"].get(field)) for f in features
                    if f["properties"].get(field) not in (None, "")]
            if vals:
                rec["min"] = min(vals)
                rec["max"] = max(vals)
                rec["mean"] = round(sum(vals) / len(vals), 1)
                neg = sum(1 for v in vals if v < 0)
                if neg:
                    report["issues"].append(f"{neg} valor(es) negativo(s) en '{field}'")
        report["fields"][field] = rec
    # claves duplicadas
    keys = [f["properties"].get(key_field) for f in features]
    dups = total - len(set(keys))
    if dups:
        report["issues"].append(f"{dups} clave(s) duplicada(s) en '{key_field}'")
    # geometrias nulas
    report["key_field"] = key_field
    report["unique_keys"] = len(set(keys))
    if not report["issues"]:
        report["issues"].append("Sin anomalias detectadas")
    return report


quality = {
    "generated_from": "Arkansas GIS Office - geodata.gis.arkansas.gov",
    "crs": "EPSG:4326 (WGS 84)",
    "counties": quality_for(
        counties["features"],
        {"sq_miles"} | {f"pop{y}" for y in decades}, "fips"),
    "municipalities": quality_for(
        munis["features"],
        {"sq_miles", "pop2000", "pop2010", "pop2020"}, "fips"),
    "congress": quality_for(cong["features"], set(), "district"),
}
json.dump(quality, open(os.path.join(OUT, "quality.json"), "w"), indent=2)
print("quality.json written")

print("Done.")
