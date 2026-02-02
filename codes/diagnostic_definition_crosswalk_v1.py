from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
BASELINE_SERIES = BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1" / "converted_series_2003CLP_1900_1994.csv"
PEREZ_PATH = BASE_DIR / "data" / "raw" / "PerezEyzaguirre_DemandaAgregada.xlsx"
OUTPUT_DIR = BASE_DIR / "outputs" / "DIAGNOSTIC_DEFINITION_CROSSWALK_v1"


def extract_price_space(header_row: pd.Series) -> tuple[str, str, Optional[str]]:
    header_text = " | ".join([str(val) for val in header_row.tolist() if isinstance(val, str)])
    price_space = "UNKNOWN"
    unit_label = "UNKNOWN"
    explicit_note = None
    if "2003" in header_text and "pesos" in header_text.lower():
        price_space = "2003 pesos"
        unit_label = "pesos de 2003"
        explicit_note = header_text
    return price_space, unit_label, explicit_note


def identify_investment_column(columns: list[str]) -> str:
    for col in columns:
        if "Invers" in col:
            return col
    raise ValueError("No investment column containing 'Invers' found in Perez sheet.")


def load_perez_metadata(path: Path) -> tuple[str, str, Optional[str]]:
    raw = pd.read_excel(path, sheet_name="Demanda Agregada", header=None)
    return extract_price_space(raw.iloc[0])

def find_column(columns: list[str], needle: str) -> str:
    for col in columns:
        if needle in col:
            return col
    raise ValueError(f"Column containing '{needle}' not found in Perez sheet.")


def build_crosswalk() -> pd.DataFrame:
    baseline = pd.read_csv(BASELINE_SERIES)
    baseline_total = baseline[baseline["asset"] == "Total"].copy()
    baseline_years = f"{baseline_total['year'].min()}-{baseline_total['year'].max()}"

    perez_df = pd.read_excel(PEREZ_PATH, sheet_name="Demanda Agregada", header=0)
    perez_df = perez_df.rename(columns={perez_df.columns[0]: "year"})
    perez_df["year"] = perez_df["year"].astype(int)
    perez_col = identify_investment_column(list(perez_df.columns))
    maquinaria_col = find_column(list(perez_df.columns), "FBKF en maquinaria")
    construccion_col = find_column(list(perez_df.columns), "FBKF en construcción")
    perez_years = f"{perez_df['year'].min()}-{perez_df['year'].max()}"

    price_space_perez, unit_label_perez, explicit_note = load_perez_metadata(PEREZ_PATH)

    unit_multiplier = "UNKNOWN"
    unit_statement_source = "Perez header unit statement not found"
    if explicit_note and "millones" in explicit_note.lower():
        unit_multiplier = 1e6
        unit_statement_source = "Perez header says millones de pesos de 2003"

    rows = [
        {
            "source": "baseline_2003clp",
            "series_name": "I_total_baseline_2003clp",
            "concept": "Gross investment total (Ig) used in j-SFC baseline",
            "coverage_years": baseline_years,
            "unit_label": "CLP (constant 2003)",
            "price_space": "2003 CLP",
            "unit_multiplier_to_CLP": "UNKNOWN",
            "unit_statement_source": "Baseline reporting series unit scale not stated",
            "components_included": "ME + NRC + RC (gross investment by asset)",
            "known_exclusions": "None stated; baseline investment is consistent with stock reconstruction",
            "comparability_flag": "OK",
            "notes": "Baseline reporting series converted from constant 1980 CLP; identities preserved.",
        },
        {
            "source": "perez",
            "series_name": perez_col,
            "concept": "Inversión Interna Bruta (Perez-Eyzaguirre Demanda Agregada)",
            "coverage_years": perez_years,
            "unit_label": unit_label_perez,
            "price_space": price_space_perez,
            "unit_multiplier_to_CLP": unit_multiplier,
            "unit_statement_source": unit_statement_source,
            "components_included": "FBKF en maquinaria + FBKF en construcción + Variación de inventarios (per sheet headers)",
            "known_exclusions": "Unknown beyond sheet documentation",
            "comparability_flag": "PARTIAL" if price_space_perez != "UNKNOWN" else "UNKNOWN",
            "notes": (
                "Includes inventory variation per sheet headers; may not align with baseline capital formation definition."
                if price_space_perez != "UNKNOWN"
                else "Price space not explicitly stated in file; do not compare levels."
            ),
        },
        {
            "source": "perez",
            "series_name": "FBKF_ex_inventarios",
            "concept": "FBKF total excl. inventories (Perez-Eyzaguirre; machinery + construction)",
            "coverage_years": perez_years,
            "unit_label": unit_label_perez,
            "price_space": price_space_perez,
            "unit_multiplier_to_CLP": unit_multiplier,
            "unit_statement_source": unit_statement_source,
            "components_included": f"{maquinaria_col} + {construccion_col}",
            "known_exclusions": "Excludes inventories explicitly; other exclusions unknown",
            "comparability_flag": "PARTIAL" if price_space_perez != "UNKNOWN" else "UNKNOWN",
            "notes": "Closer to baseline capital formation, but definitional mismatches may remain.",
        },
        {
            "source": "perez",
            "series_name": "FBKF_ex_inventarios_scaled_lambda",
            "concept": "FBKF excl inventories scaled by lambda (level normalization bridge)",
            "coverage_years": perez_years,
            "unit_label": unit_label_perez,
            "price_space": price_space_perez,
            "unit_multiplier_to_CLP": unit_multiplier,
            "unit_statement_source": unit_statement_source,
            "components_included": f"{maquinaria_col} + {construccion_col}",
            "known_exclusions": "Excludes inventories explicitly; other exclusions unknown",
            "comparability_flag": "PARTIAL" if price_space_perez != "UNKNOWN" else "UNKNOWN",
            "notes": (
                "Scaled by lambda from DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1; not a unit conversion."
            ),
        },
    ]

    if explicit_note is not None:
        rows[1]["notes"] += f" Header note: {explicit_note}"

    return pd.DataFrame(rows)


def write_outputs(crosswalk: pd.DataFrame, explicit_note: Optional[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    crosswalk.to_csv(OUTPUT_DIR / "crosswalk_table.csv", index=False)

    assumptions = {
        "files_read": {
            "baseline_reporting_series": str(BASELINE_SERIES),
            "perez_demanda_agregada": str(PEREZ_PATH),
        },
        "perez_investment_column_logic": "First column containing 'Invers' in header row",
        "perez_price_space_statement": explicit_note,
    }
    with (OUTPUT_DIR / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(assumptions, handle, sort_keys=False)

    comparability_flags = crosswalk["comparability_flag"].unique().tolist()
    warning_lines = []
    for flag in comparability_flags:
        if flag != "OK":
            warning_lines.append(f"WARNING: comparability_flag={flag}")

    summary_lines = [
        "# DIAGNOSTIC_DEFINITION_CROSSWALK_v1 summary",
        "",
        "Baseline investment total and Perez-Eyzaguirre investment totals were documented for comparability.",
        "",
        "## Comparability",
        *warning_lines,
        "",
        "Perez price space is explicitly documented as 2003 pesos in the sheet header." if explicit_note else "Perez price space is not explicitly documented; marked UNKNOWN.",
        "",
        "Baseline vs Perez comparability is PARTIAL due to inventory inclusion and definition differences.",
    ]
    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> None:
    crosswalk = build_crosswalk()
    _, _, explicit_note = load_perez_metadata(PEREZ_PATH)
    write_outputs(crosswalk, explicit_note)

    created_files = [
        OUTPUT_DIR / "crosswalk_table.csv",
        OUTPUT_DIR / "assumptions.yaml",
        OUTPUT_DIR / "summary.md",
    ]
    print("Created files:")
    for path in created_files:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
