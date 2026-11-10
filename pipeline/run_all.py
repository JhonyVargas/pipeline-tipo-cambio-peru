"""
Orquestador simple: Extract -> Load -> Transform (dbt) -> Export.
Se usa igual en local y en GitHub Actions:  python pipeline/run_all.py
"""
import subprocess
import sys


def paso(nombre: str, cmd: list[str]) -> None:
    print(f"\n{'=' * 60}\n▶ {nombre}\n{'=' * 60}", flush=True)
    resultado = subprocess.run(cmd)
    if resultado.returncode != 0:
        print(f"✖ Falló el paso: {nombre}")
        sys.exit(resultado.returncode)


if __name__ == "__main__":
    py = sys.executable
    dbt = [py, "-m", "dbt.cli.main"]
    flags = ["--project-dir", "dbt_tipo_cambio", "--profiles-dir", "dbt_tipo_cambio"]

    paso("1. Extract + Load (API BCRP -> DuckDB)", [py, "pipeline/extract.py"])
    paso("2. Transform + Test (dbt build)", dbt + ["build"] + flags)
    paso("3. Export (marts -> Parquet)", [py, "pipeline/export.py"])
    print("\n✔ Pipeline completado")
