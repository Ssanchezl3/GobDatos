# Entrega 2 — De lago a sistema que se puede ver, usar y defender

**Grupo:** Santiago Sanchez Lara
**Ciudad / territorio:** Estado de Arkansas (EE. UU.)
**Sistema publicado:** https://ssanchezl3.github.io/GobDatos/
**Repositorio:** https://github.com/Ssanchezl3/GobDatos
**Diccionario (Excel):** [`docs/diccionario_lago.xlsx`](diccionario_lago.xlsx)
**Fecha real de prueba de las fuentes:** 2026-10-20

> No se puso compuerta/clave; el sistema es público. Si se pusiera, la clave se enviaría
> aparte y nunca estaría en el repositorio.

---

## PARTE A — Las 6 preguntas de la primera entrega

### 1. ¿Para quién es su sistema y qué preguntas responde?

El sistema es para **ciudadanía, periodistas y personas que planifican** en Arkansas:
alguien que quiere entender su estado sin saber de SIG ni de bases de datos.

Responde, con datos reales y a un clic:

- **¿Dónde vive la gente y cómo cambió entre 1900 y 2020?** (mapa de condados con la
  población por década y una curva histórica por condado).
- **¿Cómo se compara Arkansas con un estado grande como Texas?** (vista 3D que levanta
  cada condado según su población y su crecimiento 2000–2020).
- **¿Cómo es el clima por zona?** (90 estaciones meteorológicas con temperatura y lluvia).

De las seis preguntas de la primera entrega, el **sistema responde dos dentro de la
interfaz** (pestaña *Preguntas*): la **1** (para quién es) y la **2** (las fuentes). Las
otras cuatro quedan **declaradas como pendientes** en esa misma pestaña, con una respuesta
breve, para ser honestos sobre el alcance.

### 2. Las fuentes que sostienen el lago

Tres fuentes **reales**, oficiales y **sin API key**, cada una con su script de ingesta.
El registro único de procedencia está en `web/data/sources.json`, y en el sistema **cada
cifra muestra a un clic** su ID de fuente, su vigencia y la fecha en que se probó.

| ID | Fuente | Qué aporta | Vigencia | Script de ingesta | API key |
|----|--------|-----------|----------|-------------------|---------|
| **F01** | Arkansas GIS Office | Límites de condados, municipios y distritos + población censal 1900–2020 | Límites vigentes; censo decadal 1900–2020 | `scripts/process_data.py` | No |
| **F02** | U.S. Census Bureau | Geometría y población de condados de Arkansas y Texas | Censos 2000, 2010, base 2020 | `scripts/build_compare.py` | No |
| **F03** | NOAA NCEI | Normales climáticas por estación (temperatura, precipitación) | Normales de 30 años, 1991–2020 | `scripts/build_climate.py` | No |

Licencias (texto completo y enlaces en `sources.json` y en el Excel):
F01 datos públicos del Estado de Arkansas; **F02 y F03 obra del gobierno de EE. UU. en
dominio público**.

### 3. Lo que dejaron por fuera

- **Todo dato a nivel de persona**: nombres, direcciones, parcelas, registros individuales.
- Capas muy pesadas o de resolución fina que no aportaban a las preguntas (p. ej.
  geometrías originales de ~17 MB; se simplificaron preservando la topología).
- Series de clima por debajo del nivel de estación (no se publican estaciones como si
  fueran personas).

Criterio: se publica **solo lo agregado por zona** (condado / municipio / estación). Si
un dato no ayuda a responder una de las preguntas, no entra.

### 4. La IA en la búsqueda

La IA se usó para **localizar las fuentes keyless** (los endpoints REST de Arkansas GIS,
TIGERweb y los CSV estáticos del Census y de NOAA) y para **depurar la ingesta**. La
bitácora completa —con aciertos y errores— está en la Parte C de este documento y en el
README. Lo importante: la IA aceleró la búsqueda, pero **cada fuente se verificó a mano**
(fecha de prueba 2026-10-20) y el lago se valida con un script automático.

### 5. El dato que podría hacer daño

El dato más sensible sería la **ubicación precisa de personas** (dónde vive o se mueve
alguien). El sistema **nunca** publica eso.

Mitigación aplicada: todo se **agrega por zona** (condado, municipio o estación
meteorológica). No hay ninguna fila que corresponda a un individuo. Así, aunque el sitio
es público y estático, no hay forma de reidentificar a nadie a partir de lo publicado.

### 6. Lo que no encontraron

- **Series de clima anteriores a 1991** a nivel de zona pequeña **sin API key**.
- Algunos **municipios con `pop2000` nulo** (2 de 200): el sistema lo muestra
  transparentemente en la pestaña *Calidad* (completitud 99 %).
- Una fuente pública y agregada que permitiera cruzar salud o economía por zona sin
  requerir llave paga, dentro del tiempo de la entrega.

---

## PARTE B — Lo mínimo que debe cumplir el sistema

| Requisito | ¿Cumple? | Cómo |
|-----------|----------|------|
| ≥3 fuentes integradas de verdad, con script de ingesta | ✅ | F01, F02, F03 (ver tabla Parte A.2); scripts en `scripts/` |
| Abre bien desde un teléfono | ✅ | Diseño responsive; en móvil la barra lateral y los KPIs se reacomodan y, en la vista 3D, los mapas se apilan |
| Cada cifra muestra su fuente a un clic (ID F0X, vigencia, fecha de prueba) | ✅ | Clic en cualquier KPI → ventana de procedencia con fuente, vigencia, fecha de prueba y licencia |
| Al menos una vista sobre el territorio | ✅ | Mapa por condado, por municipio, por distrito, estaciones por punto y vista 3D |
| Responde ≥2 preguntas de la primera entrega y dice cuáles quedan pendientes | ✅ | Pestaña *Preguntas*: responde 1 y 2; declara 3, 4, 5 y 6 como pendientes |
| Ningún dato de personas a la vista | ✅ | Solo agregados por zona |
| Datos simulados/PROXY marcados como tales | ✅ | No hay datos PROXY; la política queda declarada (si se añaden, se marcarán `PROXY`) |
| Ninguna pieza depende de llave paga ni tarjeta | ✅ | Verificado en `sources.json` y por `scripts/verify_lake.py` (`api_key_required: No`) |

**Verificación del lago** (salida real de `python scripts/verify_lake.py`):

```
 VERIFICACIÓN DEL LAGO DE DATOS
  OK   Registro de fuentes: ['F01', 'F02', 'F03']
  OK   [counties.geojson] OK — 75 features, fuente F01, clave 'fips'
  OK   [municipalities.geojson] OK — 200 features, fuente F01, clave 'fips'
  OK   [congress.geojson] OK — 4 features, fuente F01, clave 'district'
  OK   [compare.geojson] OK — 329 features, fuente F02, clave 'geoid'
  OK   [climate.geojson] OK — 90 features, fuente F03, clave 'station_id'
  6 comprobaciones OK · 0 avisos · 0 errores
```

---

## PARTE C — Bitácora de exploración (herramientas de visualización)

Se probaron varias herramientas con los **mismos datos** antes de decidir.

| Herramienta | Qué pidió para empezar | Licencia | Dónde quedan los datos al publicar | Qué resolvió | Qué no resolvió | ¿Quedó? |
|-------------|------------------------|----------|-------------------------------------|--------------|-----------------|---------|
| **Leaflet** | Incluir el JS por CDN; nada más | BSD-2 (libre) | Archivos estáticos en GitHub Pages (el dato no sale de tu repo) | Mapas por zona, coroplético, interacción, control total del HTML/estilo | Nada de 3D nativo | **Sí** (vista 2D) |
| **MapLibre GL JS** | JS por CDN; estilo de mapa sin API key | BSD-3 (libre) | Estáticos en GitHub Pages | Extrusión 3D por población, cámaras sincronizadas AR vs TX | Curva de aprendizaje mayor que Leaflet | **Sí** (vista 3D) |
| **kepler.gl** | Node/React y empaquetado del proyecto | MIT | Según hosting; configuración más pesada | 3D y hexbin muy vistosos | Difícil de incrustar como sitio estático simple y liviano | No |
| **Datawrapper** | Cuenta en su plataforma | Freemium | **Los datos quedan en servidores del proveedor** | Gráficos rápidos y bonitos | Dependencia de un tercero y menos control; choca con "defender el dato" | No |
| **Streamlit** | Python + un servidor siempre encendido | Apache-2 | Necesita backend corriendo (no es estático) | Apps de datos rápidas | No encaja con hosting estático gratis sin tarjeta (GitHub Pages) | No |

**Decisión final:** **Leaflet (2D) + MapLibre (3D)**. Ambas son libres, 100 % estáticas
(los datos no salen del repositorio) y no exigen cuenta de pago ni backend.

---

## PARTE D — Decisiones del README (en pocas líneas)

- **Qué decidimos mostrar:** agregados por zona — población (1900–2020), densidad,
  crecimiento, clase legal municipal y clima por estación. Nada individual.
- **¿Se pueden usar los datos?** Sí. F01 son datos públicos del Estado de Arkansas;
  F02 y F03 son obra del gobierno de EE. UU. en dominio público.
- **Cómo los protegimos:** publicando solo agregados por zona, sin PII, en un sitio
  estático sin backend ni credenciales que puedan filtrarse.
- **Con qué herramienta:** Leaflet + MapLibre, por ser libres, estáticas y sin API key.

---

## PARTE E — Bitácora de IA (los errores valen tanto como los aciertos)

- **Acierto:** la IA localizó los endpoints *keyless* reales (ArcGIS REST de Arkansas,
  TIGERweb del Census, normales mensuales de NOAA) y el patrón para descargar el clima
  estación por estación.
- **Error → corregido:** se asumió que la *Census Data API* era keyless; devolvía
  `missing_key.html`. Se cambió a los **CSV estáticos** de Population Estimates.
- **Error → corregido:** el filtro de condados fallaba porque `SUMLEV` venía como `"050"`
  y el código esperaba `"50"`; los totales salían en 0 hasta normalizarlo.
- **Error → corregido:** el inventario de estaciones de NOAA es *fixed-width* con columnas
  corridas; el parseo por posiciones daba 0 estaciones. Se pasó a separar por espacios.
- **Error → corregido:** el anillo de completitud (pestaña Calidad) no se pintaba por un
  problema de CSS con `conic-gradient`; se ajustó la máscara interior.
- **Acierto:** se automatizó una verificación (`verify_lake.py`) que detecta datasets
  faltantes, geometrías vacías, claves duplicadas y fuentes no registradas.

---

## PARTE F — Dos reflexiones del taller

- **Sobre datos.** Publicar *menos* puede ser mejor gobernanza. Agregar por zona responde
  las preguntas útiles sin exponer a nadie; el valor está en la **pregunta que contesta el
  dato**, no en su granularidad máxima. Un diccionario y un control de calidad honesto
  (mostrar el 99 % de completitud, no esconderlo) generan más confianza que un dato "perfecto".

- **Sobre seguridad.** Un sistema que **no depende de llaves ni backend** es más fácil de
  *defender*: no hay secretos que filtrar ni servidor que vulnerar. La **trazabilidad**
  (cada cifra con su fuente y su fecha de prueba) convierte la transparencia en una defensa,
  no en un riesgo: cualquiera puede auditar de dónde salió cada número.

---

## PARTE G — Para la presentación en clase (sin diapositivas)

Con el sistema abierto en pantalla, el grupo responde:

- **¿Qué herramienta descartaron que casi eligen?** *Datawrapper* (bonita y rápida, pero
  los datos quedaban en servidores de un tercero, lo que choca con "defender el dato"),
  y *kepler.gl* (3D muy vistoso, descartada por ser difícil de incrustar como sitio
  estático liviano).
- **¿Qué decidieron no mostrar?** Cualquier dato a nivel de persona: ubicación precisa,
  direcciones, registros individuales. Solo se publican agregados por zona.
- **¿Qué tendría que cambiar para que la respuesta fuera otra?** Si existiera una fuente
  pública **ya agregada** que no permitiera reidentificar a nadie, podríamos mostrar
  variables más sensibles (salud, ingreso) por zona; o si el hosting permitiera un backend
  seguro, podríamos usar una herramienta como Streamlit sin romper la regla de "sin tarjeta".

---

## Anexo — Cómo reproducir el lago

```bash
# dependencias (carpeta aislada para no tocar el sistema)
pip install --target=.pylibs shapely openpyxl   # en Windows: pip install shapely openpyxl

# Linux/Mac:
PYTHONPATH=.pylibs python3 scripts/ingest_all.py
# Windows (PowerShell), con las librerías ya instaladas en tu Python:
python scripts/ingest_all.py

# correr el sistema en local
cd web
python -m http.server 8099
# http://localhost:8099/index.html   y   /compare3d.html
```
