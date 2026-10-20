# 🗺️ Observatorio de Gobernanza de Datos Geoespaciales · Arkansas

Visualización web **interactiva** de los límites administrativos del estado de
**Arkansas (EE. UU.)**, construida con datos abiertos y oficiales bajo un enfoque
de **gobernanza de datos** (fuente autoritativa, linaje, CRS y licencia documentados).

> ℹ️ Nota: *Arkansas* es un **estado** de EE. UU., no una ciudad de Texas. El portal
> `geodata.gis.arkansas.gov` es el catálogo oficial de datos geoespaciales de ese estado.

![Vista de condados](docs/preview-counties.png)
![Distritos congresionales](docs/preview-congress.png)

## ✨ Qué muestra

Tres conjuntos de datos oficiales, conmutables desde la barra lateral:

| Capa | Unidades | Riqueza del dato |
|------|----------|------------------|
| **Condados** | 75 | Población censal por década **1900–2020** |
| **Municipios** | 200 | Clasificación legal (Primera/Segunda clase, Incorporado) y población 2000–2020 |
| **Distritos Congresionales** | 4 | División federal de la Cámara de Representantes |

### Interactividad (lo que es un *MUST*)
- 🎨 **Mapa coroplético** con escala de cuantiles (población / densidad / crecimiento).
- 🕰️ **Línea de tiempo animada**: desliza o reproduce la evolución de 1900 a 2020.
- 📈 **Gráficos históricos**: serie del estado y, al hacer clic en un condado, su propia curva de 120 años.
- 🧭 **KPIs en vivo** que se recalculan según la capa y el año.
- 🪧 **Tarjetas al pasar el cursor** con cifras de cada unidad.
- 📋 **Ficha de Gobernanza** con fuente, servicio, CRS (EPSG:4326), licencia y linaje.

## 🏛️ Gobernanza de datos

| Atributo | Valor |
|----------|-------|
| Fuente autoritativa | Arkansas GIS Office |
| Portal | https://geodata.gis.arkansas.gov/ |
| Servicio | ArcGIS REST · `FEATURESERVICES/Boundaries/FeatureServer` |
| Sistema de referencia | EPSG:4326 (WGS 84) |
| Licencia | Dominio público |
| Linaje | API REST → simplificación topológica (Shapely) → GeoJSON compacto |

Las geometrías originales (~17 MB) se simplificaron preservando la topología a
**~280 KB** totales, para una carga web instantánea sin perder fidelidad visual.

## 🚀 Uso local

```bash
# 1) (Opcional) regenerar los datos desde la API oficial
pip install --target=.pylibs shapely
#   descarga los GeoJSON crudos en ./data y luego:
PYTHONPATH=.pylibs python3 scripts/process_data.py

# 2) servir la app
cd web
python3 -m http.server 8099
# abre http://localhost:8099
```

## 📁 Estructura

```
GobDatos/
├── scripts/process_data.py   # ETL: descarga simplificada → GeoJSON + stats
├── data/                     # GeoJSON crudos de la API (no versionados)
└── web/
    ├── index.html            # UI
    ├── style.css             # estilos (tema oscuro)
    ├── app.js                # lógica Leaflet + coroplético + animación + gráficos
    └── data/                 # datasets procesados servidos al navegador
        ├── counties.geojson
        ├── municipalities.geojson
        ├── congress.geojson
        └── stats.json
```

## 🛠️ Tecnología
- [Leaflet](https://leafletjs.com/) para el mapa
- Basemap sin API key: Esri *World Dark Gray Canvas*
- SVG puro para los gráficos (sin dependencias de charting)
- [Shapely](https://shapely.readthedocs.io/) para la simplificación geométrica

---
Datos cortesía de la **Arkansas GIS Office** · dominio público.
