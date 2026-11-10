"""
EXPORT
Exporta las tablas finales (marts) de dbt a archivos Parquet en /data.
El dashboard de Streamlit lee estos archivos (livianos y versionados en Git).
"""
import json
import os
from datetime import datetime, timezone

import duckdb

DB_PATH = os.getenv("DUCKDB_PATH", "warehouse/tipo_cambio.duckdb")
OUT_DIR = "data"
MARTS = ["fct_tipo_cambio_diario", "fct_tipo_cambio_mensual", "fct_tipo_cambio_anual"]

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    con = duckdb.connect(DB_PATH, read_only=True)
    for tabla in MARTS:
        destino = f"{OUT_DIR}/{tabla}.parquet"
        con.execute(f"COPY (SELECT * FROM main_marts.{tabla}) TO '{destino}' (FORMAT PARQUET)")
        n = con.execute(f"SELECT count(*) FROM main_marts.{tabla}").fetchone()[0]
        print(f"[export] {tabla}: {n} filas -> {destino}")

    ultima = con.execute("SELECT max(fecha) FROM main_marts.fct_tipo_cambio_diario").fetchone()[0]
    con.close()

    meta = {
        "actualizado_en_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "ultima_fecha_dato": str(ultima),
        "fuente": "BCRP - API de Series Estadísticas",
    }
    with open(f"{OUT_DIR}/metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[export] metadata: {meta}")
