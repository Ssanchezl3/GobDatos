#!/usr/bin/env python3
"""
ORQUESTADOR DEL LAGO — ejecuta toda la ingesta, el registro de fuentes,
el diccionario en Excel y la verificación, en orden.

Uso:
    PYTHONPATH=.pylibs python3 scripts/ingest_all.py
"""
import runpy
import os
import sys

HERE = os.path.dirname(__file__)
STEPS = [
    ("F01 · Arkansas GIS (process_data)", "process_data.py"),
    ("F02 · US Census (build_compare)", "build_compare.py"),
    ("F03 · NOAA clima (build_climate)", "build_climate.py"),
    ("Registro de fuentes (build_sources)", "build_sources.py"),
    ("Diccionario Excel (build_dictionary_xlsx)", "build_dictionary_xlsx.py"),
]

for title, script in STEPS:
    print(f"\n===== {title} =====")
    runpy.run_path(os.path.join(HERE, script), run_name="__main__")

print("\n===== Verificación del lago =====")
rc = runpy.run_path(os.path.join(HERE, "verify_lake.py"), run_name="__main__")
