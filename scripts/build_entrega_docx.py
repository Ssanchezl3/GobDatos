#!/usr/bin/env python3
"""
Genera docs/ENTREGA.docx — documento de entrega con todas las respuestas,
formateado en Word, a partir del contenido de ENTREGA.md (tablas incluidas).
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
out = os.path.join(DOCS, "ENTREGA.docx")

doc = Document()

# estilo base
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)


def h(text, level=1):
    p = doc.add_heading(text, level=level)
    return p


def para(text, bold=False, italic=False, size=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold; r.italic = italic
    if size:
        r.font.size = Pt(size)
    return p


def bullets(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def table(headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    hdr = t.rows[0].cells
    for i, htext in enumerate(headers):
        hdr[i].text = htext
        for p in hdr[i].paragraphs:
            for r in p.runs:
                r.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    return t


# ---------- PORTADA ----------
title = doc.add_heading("Entrega 2 — De lago a sistema que se puede ver, usar y defender", 0)
para("Grupo: Santiago Sanchez Lara", bold=True)
doc.add_paragraph("Ciudad / territorio: Estado de Arkansas (EE. UU.)")

p = doc.add_paragraph()
p.add_run("Sistema publicado: ").bold = True
p.add_run("https://ssanchezl3.github.io/GobDatos/")
p = doc.add_paragraph()
p.add_run("Repositorio: ").bold = True
p.add_run("https://github.com/Ssanchezl3/GobDatos")
p = doc.add_paragraph()
p.add_run("Diccionario (Excel): ").bold = True
p.add_run("docs/diccionario_lago.xlsx")
p = doc.add_paragraph()
p.add_run("Fecha real de prueba de las fuentes: ").bold = True
p.add_run("2026-10-20")
para("No se puso compuerta/clave; el sistema es público. Si se pusiera, la clave se "
     "enviaría aparte y nunca estaría en el repositorio.", italic=True)

# ---------- PARTE A ----------
h("Parte A — Las 6 preguntas de la primera entrega", 1)

h("1. ¿Para quién es su sistema y qué preguntas responde?", 2)
para("El sistema es para ciudadanía, periodistas y personas que planifican en Arkansas: "
     "alguien que quiere entender su estado sin saber de SIG ni de bases de datos.")
para("Responde, con datos reales y a un clic:")
bullets([
    "¿Dónde vive la gente y cómo cambió entre 1900 y 2020? (mapa de condados con población "
    "por década y curva histórica por condado).",
    "¿Cómo se compara Arkansas con un estado grande como Texas? (vista 3D que levanta cada "
    "condado según su población y su crecimiento 2000–2020).",
    "¿Cómo es el clima por zona? (90 estaciones meteorológicas con temperatura y lluvia).",
])
para("De las seis preguntas, el sistema responde dos dentro de la interfaz (pestaña "
     "Preguntas): la 1 y la 2. Las otras cuatro quedan declaradas como pendientes en esa "
     "misma pestaña, para ser honestos sobre el alcance.")

h("2. Las fuentes que sostienen el lago", 2)
para("Tres fuentes reales, oficiales y sin API key, cada una con su script de ingesta. El "
     "registro de procedencia está en web/data/sources.json; en el sistema cada cifra "
     "muestra a un clic su ID de fuente, su vigencia y la fecha en que se probó.")
table(
    ["ID", "Fuente", "Qué aporta", "Vigencia", "Script", "API key"],
    [
        ["F01", "Arkansas GIS Office", "Límites + población 1900–2020",
         "Límites vigentes; censo 1900–2020", "process_data.py", "No"],
        ["F02", "U.S. Census Bureau", "Geometría y población AR y TX",
         "Censos 2000, 2010, base 2020", "build_compare.py", "No"],
        ["F03", "NOAA NCEI", "Clima por estación (temp., lluvia)",
         "Normales de 30 años, 1991–2020", "build_climate.py", "No"],
    ],
)
para("Licencias: F01 datos públicos del Estado de Arkansas; F02 y F03 obra del gobierno de "
     "EE. UU. en dominio público. (Texto completo y enlaces en sources.json y en el Excel.)")

h("3. Lo que dejaron por fuera", 2)
bullets([
    "Todo dato a nivel de persona: nombres, direcciones, parcelas, registros individuales.",
    "Capas muy pesadas o de resolución fina que no aportaban a las preguntas (las geometrías "
    "originales de ~17 MB se simplificaron preservando la topología).",
    "Series de clima por debajo del nivel de estación.",
])
para("Criterio: se publica solo lo agregado por zona (condado / municipio / estación). Si "
     "un dato no ayuda a responder una pregunta, no entra.")

h("4. La IA en la búsqueda", 2)
para("La IA se usó para localizar las fuentes keyless (endpoints REST de Arkansas GIS, "
     "TIGERweb y los CSV estáticos del Census y de NOAA) y para depurar la ingesta. La "
     "bitácora completa, con aciertos y errores, está en la Parte E. Cada fuente se "
     "verificó a mano (fecha de prueba 2026-10-20) y el lago se valida con un script.")

h("5. El dato que podría hacer daño", 2)
para("El dato más sensible sería la ubicación precisa de personas. El sistema nunca "
     "publica eso. Mitigación: todo se agrega por zona (condado, municipio o estación). No "
     "hay ninguna fila que corresponda a un individuo, así que aunque el sitio es público "
     "y estático, no hay forma de reidentificar a nadie.")

h("6. Lo que no encontraron", 2)
bullets([
    "Series de clima anteriores a 1991 a nivel de zona pequeña sin API key.",
    "2 de 200 municipios con pop2000 nulo: el sistema lo muestra en la pestaña Calidad "
    "(completitud 99 %).",
    "Una fuente pública y agregada para cruzar salud o economía por zona sin llave paga, "
    "dentro del tiempo de la entrega.",
])

# ---------- PARTE B ----------
h("Parte B — Lo mínimo que cumple el sistema", 1)
table(
    ["Requisito", "Cumple", "Cómo"],
    [
        ["≥3 fuentes con script de ingesta", "Sí", "F01, F02, F03 (scripts en /scripts)"],
        ["Abre desde el teléfono", "Sí", "Responsive; en 3D los mapas se apilan"],
        ["Cada cifra muestra su fuente a un clic", "Sí", "Clic en KPI → fuente, vigencia, fecha de prueba, licencia"],
        ["Vista sobre el territorio", "Sí", "Mapa por condado/municipio/distrito, estaciones y 3D"],
        ["Responde ≥2 preguntas, declara pendientes", "Sí", "Pestaña Preguntas: responde 1 y 2"],
        ["Ningún dato de personas a la vista", "Sí", "Solo agregados por zona"],
        ["Datos PROXY marcados", "Sí", "No hay PROXY; política declarada"],
        ["Sin llave paga ni tarjeta", "Sí", "Verificado por verify_lake.py"],
    ],
)
para("Verificación del lago (salida real de verify_lake.py): 6 comprobaciones OK · 0 avisos "
     "· 0 errores, con las 3 fuentes registradas y los 5 datasets validados.")

# ---------- PARTE C ----------
h("Parte C — Bitácora de exploración (herramientas)", 1)
table(
    ["Herramienta", "Qué pidió", "Licencia", "Datos al publicar", "Resolvió", "No resolvió", "¿Quedó?"],
    [
        ["Leaflet", "JS por CDN", "BSD-2", "Estáticos en GitHub Pages", "Mapas 2D, coroplético, control total", "Nada 3D nativo", "Sí (2D)"],
        ["MapLibre GL JS", "JS por CDN, estilo sin key", "BSD-3", "Estáticos en GitHub Pages", "Extrusión 3D, cámaras sincronizadas", "Más curva de aprendizaje", "Sí (3D)"],
        ["kepler.gl", "Node/React", "MIT", "Según hosting", "3D y hexbin vistosos", "Difícil de incrustar liviano", "No"],
        ["Datawrapper", "Cuenta en su plataforma", "Freemium", "En servidores del proveedor", "Gráficos rápidos", "Dependencia de tercero; choca con 'defender el dato'", "No"],
        ["Streamlit", "Python + servidor activo", "Apache-2", "Necesita backend", "Apps de datos rápidas", "No encaja con hosting estático gratis", "No"],
    ],
)
para("Decisión final: Leaflet (2D) + MapLibre (3D). Libres, 100 % estáticas (los datos no "
     "salen del repositorio) y sin cuenta de pago ni backend.")

# ---------- PARTE D ----------
h("Parte D — Decisiones", 1)
bullets([
    "Qué mostrar: agregados por zona (población 1900–2020, densidad, crecimiento, clase legal, clima). Nada individual.",
    "¿Se pueden usar los datos? Sí: F01 datos públicos estatales; F02 y F03 dominio público federal.",
    "Cómo los protegimos: solo agregados por zona, sin PII, sitio estático sin backend ni credenciales.",
    "Con qué herramienta: Leaflet + MapLibre (libres, estáticas, sin API key).",
])

# ---------- PARTE E ----------
h("Parte E — Bitácora de IA (aciertos y errores)", 1)
bullets([
    "Acierto: la IA localizó los endpoints keyless reales y el patrón para descargar el clima estación por estación.",
    "Error → corregido: se asumió que la Census Data API era keyless; devolvía missing_key.html. Se cambió a los CSV estáticos de Population Estimates.",
    "Error → corregido: el filtro de condados fallaba porque SUMLEV venía como '050' y no '50'; los totales salían en 0 hasta normalizar.",
    "Error → corregido: el inventario de estaciones de NOAA es fixed-width con columnas corridas; el parseo por posiciones daba 0 estaciones. Se pasó a separar por espacios.",
    "Error → corregido: el anillo de completitud no se pintaba por un problema de CSS con conic-gradient; se ajustó la máscara interior.",
    "Acierto: se automatizó una verificación (verify_lake.py) que detecta datasets faltantes, geometrías vacías, claves duplicadas y fuentes no registradas.",
])

# ---------- PARTE F ----------
h("Parte F — Dos reflexiones del taller", 1)
para("Sobre datos.", bold=True)
para("Publicar menos puede ser mejor gobernanza. Agregar por zona responde las preguntas "
     "útiles sin exponer a nadie; el valor está en la pregunta que contesta el dato, no en "
     "su granularidad máxima. Un diccionario y un control de calidad honesto generan más "
     "confianza que un dato 'perfecto'.")
para("Sobre seguridad.", bold=True)
para("Un sistema que no depende de llaves ni backend es más fácil de defender: no hay "
     "secretos que filtrar ni servidor que vulnerar. La trazabilidad (cada cifra con su "
     "fuente y su fecha de prueba) convierte la transparencia en una defensa, no en un riesgo.")

# ---------- PARTE G ----------
h("Parte G — Para la presentación en clase", 1)
bullets([
    "¿Qué herramienta descartaron que casi eligen? Datawrapper (los datos quedaban en "
    "servidores de un tercero) y kepler.gl (difícil de incrustar como sitio estático liviano).",
    "¿Qué decidieron no mostrar? Cualquier dato a nivel de persona: ubicación precisa, "
    "direcciones, registros individuales.",
    "¿Qué tendría que cambiar para que la respuesta fuera otra? Una fuente pública ya "
    "agregada que no permita reidentificar a nadie, o un hosting con backend seguro sin tarjeta.",
])

doc.save(out)
print("ENTREGA.docx generado:", out)
