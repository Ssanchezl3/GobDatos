# Observatorio de Gobernanza de Datos Geoespaciales — Arkansas

**Grupo:** Santiago Sanchez Lara

Sistema web para **ver, usar y defender** un pequeño lago de datos abiertos sobre el
estado de **Arkansas (EE. UU.)**, con trazabilidad de fuentes, diccionario, control
de calidad y verificación automatizada. Todo con fuentes oficiales, sin API key ni
tarjeta de crédito.

- **Sistema publicado:** _(se completa tras el despliegue a GitHub Pages — ver sección Despliegue)_
- **Repositorio:** https://github.com/Ssanchezl3/GobDatos
- **Diccionario (Excel):** [`docs/diccionario_lago.xlsx`](docs/diccionario_lago.xlsx)

![Vista de condados](docs/preview-counties.png)
![Comparación 3D AR vs TX](docs/preview-3d-population.png)

---

## 1. Para quién es y qué preguntas responde

Para **ciudadanía, periodistas y planificadores** de Arkansas. El sistema responde
**2** de las 6 preguntas de la primera entrega (las demás quedan declaradas como
pendientes dentro del propio sistema, pestaña **Preguntas**):

| # | Pregunta | Estado |
|---|----------|--------|
| 1 | ¿Para quién es y qué responde? | **Responde** |
| 2 | Las fuentes que sostienen el lago | **Responde** |
| 3 | Lo que dejaron por fuera | Pendiente |
| 4 | La IA en la búsqueda | Pendiente |
| 5 | El dato que podría hacer daño | Pendiente |
| 6 | Lo que no encontraron | Pendiente |

Preguntas de datos que sí contesta con cifras: *¿dónde vive y cómo cambió la gente
de Arkansas (1900–2020)?*, *¿cómo se compara con Texas?* y *¿cómo es el clima por zona?*

---

## 2. Las fuentes que sostienen el lago

Tres fuentes **reales**, cada una con su script de ingesta. El registro único está en
[`web/data/sources.json`](web/data/sources.json); en el sistema, **cada cifra muestra a
un clic** su fuente (ID), su vigencia y la fecha en que se probó.

| ID | Fuente | Qué aporta | Script | API key |
|----|--------|-----------|--------|---------|
| **F01** | Arkansas GIS Office | Límites (condados, municipios, distritos) + población 1900–2020 | `scripts/process_data.py` | No |
| **F02** | U.S. Census Bureau | Geometría y población de condados AR + TX (2000/2010/2020) | `scripts/build_compare.py` | No |
| **F03** | NOAA NCEI | Normales climáticas 1991–2020 por estación (temperatura, lluvia) | `scripts/build_climate.py` | No |

**Fecha real de prueba de acceso: 2026-10-20.** Licencias (resumidas; texto completo y
enlaces en `sources.json` y en el Excel): F01 datos públicos del Estado de Arkansas;
F02 y F03 obra del gobierno de EE. UU. en dominio público.

---

## 3. Lo que dejaron por fuera (y protección de datos)

- **Nada a nivel de persona**: sin nombres, direcciones ni parcelas. Solo agregados por
  zona (condado / municipio / estación).
- **El dato que podría hacer daño (pregunta 5):** la ubicación precisa de personas. Se
  mitiga publicando únicamente agregados por zona; ningún dato sensible queda a la vista.
- No hay datos **PROXY/simulados**: todas las cifras provienen directamente de F01/F02/F03.
  Si en el futuro se añaden estimaciones, se marcarán como `PROXY` en la interfaz.

---

## 4. Lo mínimo que cumple el sistema

- [x] **≥3 fuentes** integradas de verdad, con script de ingesta en el repo (F01, F02, F03).
- [x] **Abre desde el teléfono** (diseño responsive; la barra lateral se adapta).
- [x] **Cada cifra muestra su fuente a un clic** (ID F0X + vigencia + fecha de prueba).
- [x] **Vista sobre el territorio** (mapa por condado/municipio y estaciones por punto; además vista 3D).
- [x] **Responde ≥2 preguntas** y declara las pendientes (pestaña Preguntas).
- [x] **Ningún dato de personas** a la vista; lo sensible se agrega por zona.
- [x] Datos **PROXY** marcados como tales (no hay por ahora; política declarada).
- [x] **Sin llave paga ni tarjeta**: verificado en `sources.json` y por `verify_lake.py`.

---

## 5. Cómo se arma y se verifica el lago

```bash
# dependencias locales (en carpeta aislada para no tocar el sistema)
pip install --target=.pylibs shapely openpyxl

# construir TODO el lago + registro de fuentes + Excel + verificación
PYTHONPATH=.pylibs python3 scripts/ingest_all.py

# o por partes:
PYTHONPATH=.pylibs python3 scripts/process_data.py        # F01
PYTHONPATH=.pylibs python3 scripts/build_compare.py       # F02
PYTHONPATH=.pylibs python3 scripts/build_climate.py       # F03
python3 scripts/build_sources.py                          # registro F01-F03
PYTHONPATH=.pylibs python3 scripts/build_dictionary_xlsx.py  # Excel
python3 scripts/verify_lake.py                            # verificación (sale 1 si falla)
```

### Correr el sistema en local

```bash
cd web && python3 -m http.server 8099
# Vista principal: http://localhost:8099/index.html
# Vista 3D:        http://localhost:8099/compare3d.html
```

---

## 6. Bitácora de exploración de herramientas de visualización

Se probaron varias herramientas con los mismos datos antes de decidir.

| Herramienta | Qué pidió para empezar | Licencia | Dónde quedan los datos al publicar | Resolvió | No resolvió | ¿Quedó? |
|-------------|------------------------|----------|-------------------------------------|----------|-------------|---------|
| **Leaflet** (elegida 2D) | Solo incluir el JS por CDN | BSD-2 (libre) | Archivos estáticos en GitHub Pages (el dato no sale de tu repo) | Mapas por zona, coroplético, interacción, control total del HTML | Nada 3D nativo | **Sí** |
| **MapLibre GL JS** (elegida 3D) | JS por CDN; estilo sin API key | BSD-3 (libre) | Estáticos en GitHub Pages | Extrusión 3D por población, cámaras sincronizadas | Curva de aprendizaje mayor que Leaflet | **Sí** |
| **kepler.gl** | Node/React y empaquetado | MIT | Según hosting; config más pesada | 3D y hexbin muy vistosos | Difícil de incrustar como sitio estático simple y liviano | No |
| **Datawrapper** | Cuenta en su plataforma | Freemium | **Los datos quedan en sus servidores** | Gráficos rápidos y bonitos | Dependencia de un tercero y menos control; choca con “defender el dato” | No |
| **Streamlit** | Python + servidor siempre activo | Apache-2 | Necesita un backend corriendo (no es estático) | Apps de datos rápidas | No encaja con GitHub Pages (hosting estático gratis sin tarjeta) | No |

**Decisión:** Leaflet (2D) + MapLibre (3D). Ambas son libres, 100 % estáticas (los datos
no salen del repositorio del grupo) y no exigen cuenta de pago ni backend.

---

## 7. Decisiones (resumen)

- **Qué mostrar:** agregados por zona (población, crecimiento, clase legal, clima). Nada individual.
- **¿Se pueden usar los datos?** Sí: F01 datos públicos estatales; F02/F03 dominio público federal.
- **Cómo se protegieron:** solo agregados por zona; sin PII; sitio estático sin backend ni credenciales.
- **Con qué herramienta:** Leaflet + MapLibre (libres, estáticas, sin API key).

---

## 8. Bitácora de IA (aciertos y errores)

- **Acierto:** la IA localizó los endpoints *keyless* reales (ArcGIS REST de Arkansas,
  TIGERweb, NOAA NCEI) y el patrón de descarga de normales por estación.
- **Error → corregido:** se asumió que la Census Data API era keyless; devolvía
  `missing_key.html`. Se cambió a los **CSV estáticos** de Population Estimates.
- **Error → corregido:** el filtro de condados fallaba porque `SUMLEV` venía como `"050"`
  y no `"50"`; los totales salían en 0 hasta normalizar el código.
- **Error → corregido:** el inventario de estaciones NOAA es *fixed-width* con columnas
  corridas; el parseo por posiciones daba 0 estaciones. Se pasó a separar por espacios.
- **Acierto:** se automatizó una verificación (`verify_lake.py`) que detecta datasets
  faltantes, geometrías vacías, claves duplicadas y fuentes no registradas.

---

## 9. Dos reflexiones del taller

- **Sobre datos:** publicar *menos* puede ser mejor gobernanza. Agregar por zona
  responde las preguntas útiles sin exponer a nadie; el valor está en la pregunta que
  contesta el dato, no en su granularidad máxima.
- **Sobre seguridad:** un sistema que no depende de llaves ni backend es más fácil de
  *defender*: no hay secretos que filtrar ni servidor que vulnerar. La trazabilidad
  (cada cifra con su fuente y fecha de prueba) convierte la transparencia en una
  defensa, no en un riesgo.

---

## 10. Despliegue en GitHub Pages

El sitio es 100 % estático (carpeta `web/`). Para publicarlo gratis, sin tarjeta:

1. En GitHub: **Settings → Pages**.
2. **Source:** *Deploy from a branch*; **Branch:** `main`; **Folder:** `/web` (si la opción
   de carpeta no aparece, usar la acción incluida en `.github/workflows/pages.yml`).
3. GitHub publica en `https://ssanchezl3.github.io/GobDatos/`.

La URL final se pega arriba, en **Sistema publicado**, con los nombres del grupo ya
visibles dentro del sistema. Si se pone una compuerta/clave, **no** va en el repositorio.

---

## Estructura del repositorio

```
GobDatos/
├── scripts/
│   ├── ingest_all.py            # orquesta toda la ingesta + verificación
│   ├── process_data.py          # F01  Arkansas GIS
│   ├── build_compare.py         # F02  US Census (AR vs TX)
│   ├── build_climate.py         # F03  NOAA clima
│   ├── build_sources.py         # registro de fuentes F01-F03
│   ├── build_dictionary_xlsx.py # diccionario del lago en Excel
│   └── verify_lake.py           # verificación del lago
├── docs/
│   └── diccionario_lago.xlsx    # diccionario (solo lo que está en el lago)
└── web/                         # SISTEMA (sitio estático)
    ├── index.html · style.css · app.js          # vista 2D (Leaflet)
    ├── compare3d.html · .css · .js              # vista 3D (MapLibre)
    └── data/                                    # el lago publicado
        ├── sources.json                         # registro de fuentes (F01-F03)
        ├── counties / municipalities / congress .geojson   (F01)
        ├── compare.geojson                      (F02)
        ├── climate.geojson                      (F03)
        └── dictionary.json · quality.json · stats.json
```

---
Datos: **Arkansas GIS Office** (F01), **U.S. Census Bureau** (F02) y **NOAA NCEI** (F03).
Todo dominio público / datos abiertos.
