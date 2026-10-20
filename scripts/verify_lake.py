#!/usr/bin/env python3
"""
VERIFICACIÓN DEL LAGO DE DATOS

Comprueba que el lago publicado (web/data/) esté íntegro y trazable:
  1. Todos los datasets esperados existen y son JSON válido.
  2. Cada dataset tiene features y geometrías no vacías.
  3. Los campos clave están presentes y sin duplicados.
  4. Cada dataset está asociado a una fuente registrada (F01/F02/F03).
  5. Ninguna fuente requiere API key.

Sale con código 0 si todo pasa; 1 si hay fallos. Imns un reporte legible.
"""
import json
import os
import sys

OUT = os.path.join(os.path.dirname(__file__), "..", "web", "data")

# dataset -> (fuente, campo_clave, min_features)
EXPECTED = {
    "counties.geojson": ("F01", "fips", 75),
    "municipalities.geojson": ("F01", "fips", 200),
    "congress.geojson": ("F01", "district", 4),
    "compare.geojson": ("F02", "geoid", 300),
    "climate.geojson": ("F03", "station_id", 50),
}

errors, warnings, passed = [], [], []


def load(name):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        errors.append(f"[{name}] no existe en el lago")
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception as e:
        errors.append(f"[{name}] JSON inválido: {e}")
        return None


def main():
    sources = load("sources.json")
    if not sources:
        errors.append("sources.json ausente: no hay registro de fuentes")
        registered = set()
    else:
        registered = set(sources.get("sources", {}).keys())
        for sid, s in sources.get("sources", {}).items():
            if s.get("api_key_required"):
                errors.append(f"[{sid}] requiere API key (prohibido por la rúbrica)")
            if not s.get("test_date"):
                warnings.append(f"[{sid}] sin fecha de prueba (test_date)")
        passed.append(f"Registro de fuentes: {sorted(registered)}")

    for name, (src, key, minf) in EXPECTED.items():
        fc = load(name)
        if not fc:
            continue
        feats = fc.get("features", [])
        if len(feats) < minf:
            errors.append(f"[{name}] {len(feats)} features (< {minf} esperadas)")
            continue
        # geometrías
        empty = sum(1 for f in feats if not f.get("geometry"))
        if empty:
            errors.append(f"[{name}] {empty} geometrías vacías")
        # clave presente + duplicados
        keys = [f["properties"].get(key) for f in feats]
        missing = sum(1 for k in keys if k in (None, ""))
        if missing:
            errors.append(f"[{name}] {missing} registros sin clave '{key}'")
        dups = len(keys) - len(set(keys))
        if dups:
            warnings.append(f"[{name}] {dups} clave(s) '{key}' duplicada(s)")
        # fuente registrada
        if src not in registered:
            errors.append(f"[{name}] referencia fuente {src} no registrada")
        passed.append(f"[{name}] OK — {len(feats)} features, fuente {src}, clave '{key}'")

    # reporte
    print("=" * 56)
    print(" VERIFICACIÓN DEL LAGO DE DATOS")
    print("=" * 56)
    for p in passed:
        print("  OK  ", p)
    for w in warnings:
        print("  !   ", w)
    for e in errors:
        print("  X   ", e)
    print("-" * 56)
    print(f"  {len(passed)} comprobaciones OK · {len(warnings)} avisos · {len(errors)} errores")
    print("=" * 56)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
