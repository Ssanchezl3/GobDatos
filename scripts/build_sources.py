#!/usr/bin/env python3
"""
REGISTRO DE FUENTES DEL LAGO — genera web/data/sources.json

Es la unica fuente de verdad sobre procedencia. Cada fuente tiene un ID
(F01, F02, F03...) que el sistema usa para que CADA CIFRA muestre, a un clic:
  - de que fuente viene (ID + nombre)
  - su vigencia / periodo del dato
  - la fecha real en que se probo el acceso (test_date)
  - su licencia (texto de la fuente + enlace al original)

La fecha de prueba se fija con TEST_DATE (fecha real de verificacion del acceso).
"""
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "web", "data")
os.makedirs(OUT, exist_ok=True)

TEST_DATE = "2026-10-20"  # fecha real en que se verifico el acceso a las fuentes

SOURCES = {
    "F01": {
        "id": "F01",
        "name": "Arkansas GIS Office — Límites administrativos",
        "publisher": "Arkansas GIS Office (Department of Transformation and Shared Services)",
        "portal": "https://geodata.gis.arkansas.gov/",
        "endpoint": "https://gis.arkansas.gov/arcgis/rest/services/FEATURESERVICES/Boundaries/FeatureServer",
        "service_type": "ArcGIS REST FeatureServer (keyless)",
        "crs": "EPSG:4326 (WGS 84)",
        "coverage": "Arkansas — 75 condados, 200 municipios, 4 distritos congresionales",
        "validity": "Límites vigentes; población censal decadal 1900–2020",
        "test_date": TEST_DATE,
        "license": "Datos públicos del Estado de Arkansas; uso abierto. Ver política del portal.",
        "license_url": "https://gis.arkansas.gov/",
        "api_key_required": False,
        "ingest_script": "scripts/process_data.py",
    },
    "F02": {
        "id": "F02",
        "name": "U.S. Census Bureau — Geografía y población de condados",
        "publisher": "U.S. Census Bureau",
        "portal": "https://www.census.gov/",
        "endpoint": "TIGERweb Generalized_ACS2024/State_County + archivos Population Estimates (www2.census.gov)",
        "service_type": "ArcGIS REST + CSV estático (keyless)",
        "crs": "EPSG:4326 (WGS 84)",
        "coverage": "Arkansas (05) y Texas (48) — 329 condados; población 2000/2010/2020",
        "validity": "Censos decenales 2000, 2010 y base 2020",
        "test_date": TEST_DATE,
        "license": "Obra del gobierno de EE. UU.: dominio público (sin restricciones de uso).",
        "license_url": "https://www.census.gov/data/developers/about/terms-of-service.html",
        "api_key_required": False,
        "ingest_script": "scripts/build_compare.py",
    },
    "F03": {
        "id": "F03",
        "name": "NOAA NCEI — Normales climáticas 1991–2020 (Arkansas)",
        "publisher": "NOAA National Centers for Environmental Information (NCEI)",
        "portal": "https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals",
        "endpoint": "https://www.ncei.noaa.gov/data/normals-monthly/1991-2020/",
        "service_type": "CSV estático por estación (keyless)",
        "crs": "EPSG:4326 (WGS 84)",
        "coverage": "Arkansas — 90 estaciones meteorológicas",
        "validity": "Normales de 30 años, periodo 1991–2020",
        "test_date": TEST_DATE,
        "license": "Obra del gobierno de EE. UU.: dominio público. Se solicita citar a NOAA/NCEI.",
        "license_url": "https://www.ncei.noaa.gov/access/us-climate-normals/",
        "api_key_required": False,
        "ingest_script": "scripts/build_climate.py",
    },
}

registry = {
    "test_date": TEST_DATE,
    "note": "Cada cifra del sistema referencia uno de estos IDs. "
            "Ninguna fuente requiere llave paga ni tarjeta.",
    "sources": SOURCES,
}

json.dump(registry, open(os.path.join(OUT, "sources.json"), "w"),
          ensure_ascii=False, indent=2)
print(f"sources.json: {len(SOURCES)} fuentes (F01–F0{len(SOURCES)}), test_date {TEST_DATE}")

if __name__ == "__main__":
    pass
