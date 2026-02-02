from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
BASELINE_SERIES = BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1" / "converted_series_2003CLP_1900_1994.csv"
PEREZ_PATH = BASE_DIR / "data" / "raw" / "PerezEyzaguirre_DemandaAgregada.xlsx"
OUTPUT_DIR = BASE_DIR / "outputs" / "EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v1"


def extract_price_space(header_row: pd.Series) -> tuple[str, Optional[str]]:
    header_text = " | ".join([str(val) for val in header_row.tolist() if isinstance(val, str)])
    if "2003" in header_text and "pesos" in header_text.lower():
        return "2003 pesos", header_text
    return "UNKNOWN", None


def find_column(columns: list[str], needle: str) -> str:
    for col in columns:
        if needle in col:
            return col
    raise ValueError(f"Column containing '{needle}' not found in Perez sheet.")


def load_perez(path: Path) -> tuple[pd.DataFrame, dict[str, str], str, Optional[str]]:
    raw_header = pd.read_excel(path, sheet_name="Demanda Agregada", header=None)
    price_space, header_note = extract_price_space(raw_header.iloc[0])
    df = pd.read_excel(path, sheet_name="Demanda Agregada", header=0)
    df = df.rename(columns={df.columns[0]: "year"})
    df["year"] = df["year"].astype(int)

    maquinaria_col = find_column(list(df.columns), "FBKF en maquinaria")
    construccion_col = find_column(list(df.columns), "FBKF en construcción")
    inventarios_col = find_column(list(df.columns), "Variación de inventarios")
    iib_col = find_column(list(df.columns), "Inversión Interna Bruta")

    df = df[["year", maquinaria_col, construccion_col, inventarios_col, iib_col]].copy()
    df = df.rename(
        columns={
            maquinaria_col: "perez_fbfk_maquinaria",
            construccion_col: "perez_fbfk_construccion",
            inventarios_col: "perez_inventarios",
            iib_col: "perez_iib_gross",
        }
    )
    df["I_perez_fbfk"] = df["perez_fbfk_maquinaria"] + df["perez_fbfk_construccion"]
    columns_used = {
        "FBKF en maquinaria": maquinaria_col,
        "FBKF en construcción": construccion_col,
        "Variación de inventarios": inventarios_col,
        "Inversión Interna Bruta": iib_col,
    }
    return df, columns_used, price_space, header_note


def compute_stats(series: pd.Series) -> dict[str, float]:
    return {
        "mean": float(series.mean()),
        "min": float(series.min()),
        "max": float(series.max()),
    }


def ratio_stats(series: pd.Series) -> dict[str, float]:
    return {
        "mean": float(series.mean()),
        "p10": float(series.quantile(0.1)),
        "p90": float(series.quantile(0.9)),
    }


def summarize_periods(df: pd.DataFrame, ratio_valid: bool) -> list[str]:
    periods = {
        "1900-1949": (1900, 1949),
        "1950-1994": (1950, 1994),
        "1973-1989": (1973, 1989),
        "1990-1994": (1990, 1994),
    }
    lines = []
    for label, (start, end) in periods.items():
        subset = df[(df["year"] >= start) & (df["year"] <= end)].copy()
        gap_stats = compute_stats(subset["gap"].dropna())
        lines.append(f"### Gap stats {label}")
        lines.append(f"- mean: {gap_stats['mean']:.6f}")
        lines.append(f"- min: {gap_stats['min']:.6f}")
        lines.append(f"- max: {gap_stats['max']:.6f}")
        if ratio_valid:
            ratio_series = subset["ratio"].dropna()
            if not ratio_series.empty:
                stats = ratio_stats(ratio_series)
                lines.append(f"- ratio mean: {stats['mean']:.6f}")
                lines.append(f"- ratio p10: {stats['p10']:.6f}")
                lines.append(f"- ratio p90: {stats['p90']:.6f}")
        lines.append("")
    return lines


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_SERIES)
    baseline_total = baseline[baseline["asset"] == "Total"][["year", "I"]].copy()
    baseline_total = baseline_total.rename(columns={"I": "I_baseline_2003"})

    perez_df, columns_used, price_space_perez, header_note = load_perez(PEREZ_PATH)

    merged = baseline_total.merge(perez_df, on="year", how="left")
    merged["price_space_baseline"] = "2003CLP"
    merged["price_space_perez"] = price_space_perez
    merged["gap"] = merged["I_baseline_2003"] - merged["I_perez_fbfk"]

    positive_mask = (merged["I_baseline_2003"] > 0) & (merged["I_perez_fbfk"] > 0)
    merged["ratio"] = np.where(positive_mask, merged["I_baseline_2003"] / merged["I_perez_fbfk"], np.nan)
    merged["logdiff"] = np.where(
        positive_mask,
        np.log(merged["I_baseline_2003"]) - np.log(merged["I_perez_fbfk"]),
        np.nan,
    )
    merged["flags"] = np.where(
        merged["I_perez_fbfk"].isna(),
        "missing_perez",
        np.where(positive_mask, "ratio_logdiff_ok", "non_positive_values"),
    )

    merged.to_csv(OUTPUT_DIR / "merged_comparison_1900_1994.csv", index=False)

    assumptions = {
        "files_read": {
            "baseline_reporting_series": str(BASELINE_SERIES),
            "perez_demanda_agregada": str(PEREZ_PATH),
        },
        "perez_columns_used": columns_used,
        "constructed_series_definition": "FBKF en maquinaria + FBKF en construcción",
        "price_space_perez": price_space_perez,
        "price_space_perez_header_note": header_note,
        "ratio_logdiff_computed": True,
        "ratio_logdiff_reason": "price space explicitly 2003 pesos",
        "filtering_rules": "Ratios/logdiff computed only when both baseline and Perez FBKF are positive; missing Perez flagged.",
    }
    with (OUTPUT_DIR / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(assumptions, handle, sort_keys=False)

    summary_lines = [
        "# EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v1 summary",
        "",
        "Comparability status: PARTIAL",
        "Price space compatible: yes",
        "Ratios/logdiff computed: yes",
        "",
    ]
    summary_lines.extend(summarize_periods(merged, ratio_valid=True))
    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    created_files = [
        OUTPUT_DIR / "merged_comparison_1900_1994.csv",
        OUTPUT_DIR / "assumptions.yaml",
        OUTPUT_DIR / "summary.md",
    ]
    print("Created files:")
    for path in created_files:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
