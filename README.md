# 💱 Pipeline de Tipo de Cambio USD/PEN

Solución de **ingeniería de datos** que extrae automáticamente el tipo de cambio interbancario
publicado por el **Banco Central de Reserva del Perú (BCRP)**, lo transforma con **dbt** sobre
**DuckDB** y lo publica en un **dashboard interactivo** en Streamlit Community Cloud.

![Pipeline](https://github.com/JhonyVargas/pipeline-tipo-cambio-peru/actions/workflows/pipeline.yml/badge.svg)

🔗 **Dashboard en vivo:** https://TU-APP.streamlit.app

---

## 🏗️ Arquitectura

```
┌────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌─────────┐    ┌────────────┐
│ API BCRP   │ →  │ Python   │ →  │ DuckDB   │ →  │ dbt          │ →  │ Parquet │ →  │ Streamlit  │
│ (fuente)   │    │ Extract  │    │ raw      │    │ staging/marts│    │ /data   │    │ Dashboard  │
└────────────┘    └──────────┘    └──────────┘    └──────────────┘    └─────────┘    └────────────┘
                         ▲
                         └──── GitHub Actions (cron lunes a viernes 09:00 Lima)
```

| Capa | Herramienta | Descripción |
|------|-------------|-------------|
| Extract + Load | Python | Descarga la serie del BCRP y la guarda cruda en `raw.tipo_cambio_bcrp` |
| Almacenamiento | DuckDB | Data warehouse analítico embebido (un solo archivo) |
| Transform | dbt | Modelos `staging` → `marts` con tests de calidad |
| Orquestación | GitHub Actions | Ejecución diaria automática + commit de resultados |
| Visualización | Streamlit + Plotly | Dashboard público con KPIs y gráficos |

## 🔧 Modelos dbt

| Modelo | Capa | Contenido |
|--------|------|-----------|
| `stg_tipo_cambio` | staging | Parseo de fechas `'02.Ene.20'` → `DATE`, limpieza de `n.d.` |
| `fct_tipo_cambio_diario` | marts | Compra, venta, spread, variación diaria, medias móviles 7d/30d |
| `fct_tipo_cambio_mensual` | marts | OHLC mensual, promedio, volatilidad, variación mensual |
| `fct_tipo_cambio_anual` | marts | Resumen anual |

**Tests de calidad (13):** unicidad y no nulos en claves, rango válido de valores (2.5–5.0) y la regla
de negocio *venta ≥ compra* (configurada como advertencia: la fuente tiene 5 días históricos con esta anomalía).

## 📁 Estructura

```
├── .github/workflows/pipeline.yml   # Automatización (CI/CD del pipeline)
├── pipeline/
│   ├── extract.py                   # Extract + Load
│   ├── export.py                    # Export de marts a Parquet
│   └── run_all.py                   # Orquestador local / CI
├── dbt_tipo_cambio/                 # Proyecto dbt
│   ├── models/staging/
│   ├── models/marts/
│   └── tests/
├── app/streamlit_app.py             # Dashboard
├── data/                            # Marts en Parquet (actualizados por el bot)
├── requirements.txt                 # Dependencias del dashboard
└── requirements-pipeline.txt        # Dependencias del pipeline
```

## ▶️ Ejecutar en local

```bash
pip install -r requirements-pipeline.txt -r requirements.txt
python pipeline/run_all.py              # corre todo el pipeline
streamlit run app/streamlit_app.py      # abre el dashboard
```

## ☁️ Despliegue

1. **GitHub Actions:** el workflow corre solo (cron) o manualmente desde *Actions → Run workflow*.
   Al terminar hace commit de `data/` con los datos nuevos.
2. **Streamlit Community Cloud:** *New app* → este repositorio → rama `main` → archivo
   `app/streamlit_app.py`. Cada commit del bot redespliega el dashboard con datos frescos.

## 📊 Fuente de datos

BCRP – API de Series Estadísticas: `PD04637PD` (TC interbancario compra) y `PD04638PD` (venta).
https://estadisticas.bcrp.gob.pe/estadisticas/series/
