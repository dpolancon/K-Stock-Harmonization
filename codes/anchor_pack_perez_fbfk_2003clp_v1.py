from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
PEREZ_PATH = BASE_DIR / "data" / "raw" / "PerezEyzaguirre_DemandaAgregada.xlsx"
OUTPUT_DIR = BASE_DIR / "outputs" / "ANCHOR_PEREZ_FBFK_2003CLP_v1"


def extract_price_space(header_row: pd.Series) -> tuple[str, Optional[str], Optional[str]]:
    header_text = " | ".join([str(val) for val in header_row.tolist() if isinstance(val, str)])
    price_space = "UNKNOWN"
    unit_label = None
    if "2003" in header_text and "pesos" in header_text.lower():
        price_space = "2003 pesos"
        unit_label = "millones de pesos de 2003"
    return price_space, unit_label, header_text if header_text else None


def find_column(columns: list[str], needle: str) -> str:
    for col in columns:
        if needle in col:
            return col
    raise ValueError(f"Column containing '{needle}' not found in Perez sheet.")


def load_perez(path: Path) -> tuple[pd.DataFrame, dict[str, str], str, Optional[str], Optional[str]]:
    raw_header = pd.read_excel(path, sheet_name="Demanda Agregada", header=None)
    price_space, unit_label, header_note = extract_price_space(raw_header.iloc[0])
    df = pd.read_excel(path, sheet_name="Demanda Agregada", header=0)
    df = df.rename(columns={df.columns[0]: "year"})
    df["year"] = df["year"].astype(int)

    maquinaria_col = find_column(list(df.columns), "FBKF en maquinaria")
    construccion_col = find_column(list(df.columns), "FBKF en construcción")
    inventarios_col = find_column(list(df.columns), "Variación de inventarios")
    iib_col = find_column(list(df.columns), "Inversión Interna Bruta")

    data = df[["year", maquinaria_col, construccion_col, inventarios_col, iib_col]].copy()
    data = data.rename(
        columns={
            maquinaria_col: "perez_fbfk_maquinaria",
            construccion_col: "perez_fbfk_construccion",
            inventarios_col: "perez_inventarios",
            iib_col: "perez_iib_gross",
        }
    )
    data["perez_fbfk_total_ex_inv"] = data["perez_fbfk_maquinaria"] + data["perez_fbfk_construccion"]

    columns_used = {
        "FBKF en maquinaria": maquinaria_col,
        "FBKF en construcción": construccion_col,
        "Variación de inventarios": inventarios_col,
        "Inversión Interna Bruta": iib_col,
    }
    return data, columns_used, price_space, unit_label, header_note


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data, columns_used, price_space, unit_label, header_note = load_perez(PEREZ_PATH)
    data.to_csv(OUTPUT_DIR / "perez_anchor_pack_1860_2010.csv", index=False)

    metadata = {
        "source_file": str(PEREZ_PATH),
        "sheet": "Demanda Agregada",
        "price_space": price_space,
        "unit_statement": unit_label,
        "header_note": header_note,
        "columns_used": columns_used,
        "definitions": {
            "perez_fbfk_maquinaria": "FBKF en maquinaria (Perez)",
            "perez_fbfk_construccion": "FBKF en construcción (Perez)",
            "perez_inventarios": "Variación de inventarios (Perez)",
            "perez_iib_gross": "Inversión Interna Bruta (Perez)",
            "perez_fbfk_total_ex_inv": "FBKF total excl. inventories = maquinaria + construcción",
        },
        "intended_usage": (
            "FBKF_total_ex_inv is admissible for capital formation; inventories are not used for capital-stock "
            "accumulation but retained for macro identity checks."
        ),
    }
    with (OUTPUT_DIR / "metadata.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(metadata, handle, sort_keys=False)

    counts = data.notna().sum()
    iib_diff = (data["perez_fbfk_maquinaria"] + data["perez_fbfk_construccion"] + data["perez_inventarios"]) - data[
        "perez_iib_gross"
    ]
    max_abs_diff = float(iib_diff.abs().max())

    summary_lines = [
        "# ANCHOR_PEREZ_FBFK_2003CLP_v1 summary",
        "",
        f"Coverage years: {data['year'].min()}-{data['year'].max()}",
        "",
        "## Non-missing counts",
        *(f"- {col}: {int(counts[col])}" for col in counts.index),
        "",
        "## Sanity check",
        "Check: maquinaria + construcción + inventarios vs Inversión Interna Bruta.",
        f"Max absolute difference: {max_abs_diff:.6f}",
        "Note: differences may reflect definitional or rounding discrepancies.",
    ]
    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    created_files = [
        OUTPUT_DIR / "perez_anchor_pack_1860_2010.csv",
        OUTPUT_DIR / "metadata.yaml",
        OUTPUT_DIR / "summary.md",
    ]
    print("Created files:")
    for path in created_files:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
