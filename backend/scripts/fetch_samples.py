"""Descarga Online Retail II (UCI) y la deja como data/samples/online_retail.csv.

Transacciones reales de un retailer online del Reino Unido (2009-2011). Se usa la hoja
"Year 2010-2011" (~540k filas). Leer el Excel tarda un par de minutos.

Uso: python scripts/fetch_samples.py
"""

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
SHEET = "Year 2010-2011"


def main() -> None:
    out_dir = ROOT / "data" / "samples"
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "online_retail.csv"
    if target.exists():
        print(f"Ya existe {target}")
        return

    xlsx = raw_dir / "online_retail_II.xlsx"
    if not xlsx.exists():
        print(f"Descargando {URL} ...")
        with urllib.request.urlopen(URL, timeout=120) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        member = next((m for m in archive.namelist() if m.endswith(".xlsx")), None)
        if member is None:
            sys.exit("El zip no contiene un .xlsx")
        xlsx.write_bytes(archive.read(member))

    print(f"Leyendo hoja '{SHEET}' (tarda un poco) ...")
    df = pd.read_excel(xlsx, sheet_name=SHEET, dtype={"Invoice": str, "StockCode": str})
    df = df.dropna(subset=["Customer ID"])
    df["Customer ID"] = df["Customer ID"].astype(int)
    df.to_csv(target, index=False)
    print(f"{len(df):,} filas de {df['Customer ID'].nunique():,} clientes -> {target}")


if __name__ == "__main__":
    main()
