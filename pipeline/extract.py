"""
EXTRACT + LOAD
Descarga el tipo de cambio interbancario (compra y venta) desde la API pública
del BCRP y lo carga "tal cual" (raw) en DuckDB. La limpieza la hace dbt.
"""
import json
import os
import urllib.request
from datetime import date, datetime, timezone

import duckdb

DB_PATH = os.getenv("DUCKDB_PATH", "warehouse/tipo_cambio.duckdb")
FECHA_INICIO = os.getenv("FECHA_INICIO", "2015-01-01")

# PD04637PD = TC interbancario compra | PD04638PD = TC interbancario venta
SERIES = "PD04637PD-PD04638PD"
URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{series}/json/{ini}/{fin}"


def extraer() -> list[dict]:
    url = URL.format(series=SERIES, ini=FECHA_INICIO, fin=date.today().isoformat())
    print(f"[extract] GET {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "data-pipeline-tc/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8-sig"))

    filas = [
        {"periodo": p["name"], "compra": p["values"][0], "venta": p["values"][1]}
        for p in payload["periods"]
    ]
    print(f"[extract] {len(filas)} registros recibidos")
    return filas


def cargar(filas: list[dict]) -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    cargado_en = datetime.now(timezone.utc).replace(tzinfo=None)
    con = duckdb.connect(DB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(
        """
        CREATE OR REPLACE TABLE raw.tipo_cambio_bcrp (
            periodo    VARCHAR,   -- formato BCRP: '02.Ene.20'
            compra     VARCHAR,   -- texto, puede venir 'n.d.'
            venta      VARCHAR,
            cargado_en TIMESTAMP
        )
        """
    )
    con.executemany(
        "INSERT INTO raw.tipo_cambio_bcrp VALUES (?, ?, ?, ?)",
        [(f["periodo"], f["compra"], f["venta"], cargado_en) for f in filas],
    )
    total = con.execute("SELECT count(*) FROM raw.tipo_cambio_bcrp").fetchone()[0]
    con.close()
    print(f"[load] {total} filas en raw.tipo_cambio_bcrp ({DB_PATH})")


if __name__ == "__main__":
    cargar(extraer())
