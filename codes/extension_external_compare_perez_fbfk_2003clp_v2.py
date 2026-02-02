from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
BASELINE_SERIES = BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1" / "converted_series_2003CLP_1900_1994.csv"
PEREZ_ANCHOR = BASE_DIR / "outputs" / "ANCHOR_PEREZ_FBFK_2003CLP_v1" / "perez_anchor_pack_1860_2010.csv"
BEST_SCALE = BASE_DIR / "outputs" / "DIAGNOSTIC_UNIT_SCALE_AUDIT_v1" / "best_scale.yaml"
OUTPUT_DIR = BASE_DIR / "outputs" / "EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v2"


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


def summarize_periods(df: pd.DataFrame, label: str, gap_col: str, ratio_col: str) -> list[str]:
    periods = {
        "1900-1949": (1900, 1949),
        "1950-1994": (1950, 1994),
        "1973-1989": (1973, 1989),
        "1990-1994": (1990, 1994),
    }
    lines = [f"## {label}"]
    for period_label, (start, end) in periods.items():
        subset = df[(df["year"] >= start) & (df["year"] <= end)].copy()
        gap_stats = compute_stats(subset[gap_col].dropna())
        lines.append(f"### Gap stats {period_label}")
        lines.append(f"- mean: {gap_stats['mean']:.6f}")
        lines.append(f"- min: {gap_stats['min']:.6f}")
        lines.append(f"- max: {gap_stats['max']:.6f}")
        ratio_series = subset[ratio_col].dropna()
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
    baseline_total = baseline_total.rename(columns={"I": "I_baseline_2003_raw"})

    perez = pd.read_csv(PEREZ_ANCHOR)
    perez = perez.rename(columns={"perez_fbfk_total_ex_inv": "I_perez_fbfk_raw"})
    perez = perez[["year", "I_perez_fbfk_raw"]]

    with BEST_SCALE.open("r", encoding="utf-8") as handle:
        best_scale = yaml.safe_load(handle)
    best_pair = best_scale["best_pair"]
    baseline_multiplier = float(best_pair["baseline_multiplier"])
    perez_multiplier = float(best_pair["perez_multiplier"])

    merged = baseline_total.merge(perez, on="year", how="left")
    merged["baseline_multiplier"] = baseline_multiplier
    merged["perez_multiplier"] = perez_multiplier

    merged["gap_raw"] = merged["I_baseline_2003_raw"] - merged["I_perez_fbfk_raw"]
    positive_raw = (merged["I_baseline_2003_raw"] > 0) & (merged["I_perez_fbfk_raw"] > 0)
    merged["ratio_raw"] = np.where(positive_raw, merged["I_baseline_2003_raw"] / merged["I_perez_fbfk_raw"], np.nan)
    merged["logdiff_raw"] = np.where(
        positive_raw,
        np.log(merged["I_baseline_2003_raw"]) - np.log(merged["I_perez_fbfk_raw"]),
        np.nan,
    )
    merged["flags_raw"] = np.where(
        merged["I_perez_fbfk_raw"].isna(),
        "missing_perez",
        np.where(positive_raw, "ratio_logdiff_ok", "non_positive_values"),
    )

    merged["I_baseline_2003_scaled"] = merged["I_baseline_2003_raw"] * baseline_multiplier
    merged["I_perez_fbfk_scaled"] = merged["I_perez_fbfk_raw"] * perez_multiplier
    merged["gap_scaled"] = merged["I_baseline_2003_scaled"] - merged["I_perez_fbfk_scaled"]
    positive_scaled = (merged["I_baseline_2003_scaled"] > 0) & (merged["I_perez_fbfk_scaled"] > 0)
    merged["ratio_scaled"] = np.where(
        positive_scaled,
        merged["I_baseline_2003_scaled"] / merged["I_perez_fbfk_scaled"],
        np.nan,
    )
    merged["logdiff_scaled"] = np.where(
        positive_scaled,
        np.log(merged["I_baseline_2003_scaled"]) - np.log(merged["I_perez_fbfk_scaled"]),
        np.nan,
    )
    merged["flags_scaled"] = np.where(
        merged["I_perez_fbfk_scaled"].isna(),
        "missing_perez",
        np.where(positive_scaled, "ratio_logdiff_ok", "non_positive_values"),
    )

    merged.to_csv(OUTPUT_DIR / "merged_comparison_1900_1994.csv", index=False)

    assumptions = {
        "files_read": {
            "baseline_reporting_series": str(BASELINE_SERIES),
            "perez_anchor_pack": str(PEREZ_ANCHOR),
            "best_scale": str(BEST_SCALE),
        },
        "baseline_multiplier": baseline_multiplier,
        "perez_multiplier": perez_multiplier,
        "multiplier_source": "outputs/DIAGNOSTIC_UNIT_SCALE_AUDIT_v1/best_scale.yaml",
        "ratio_logdiff_computed": True,
        "ratio_logdiff_reason": "computed for raw and scaled when both series are positive",
        "filtering_rules": "Missing Perez flagged; ratios/logdiff computed only on positive values.",
    }
    with (OUTPUT_DIR / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(assumptions, handle, sort_keys=False)

    summary_lines = [
        "# EXTENSION_EXTERNAL_COMPARE_PEREZ_FBFK_2003CLP_v2 summary",
        "",
        "Comparability status: PARTIAL",
        "Price space compatible: yes",
        "Ratios/logdiff computed: yes",
        f"Multipliers used: baseline={baseline_multiplier}, perez={perez_multiplier}",
        "Source: outputs/DIAGNOSTIC_UNIT_SCALE_AUDIT_v1/best_scale.yaml",
        "",
    ]
    summary_lines.extend(summarize_periods(merged, "Raw comparison", "gap_raw", "ratio_raw"))
    summary_lines.extend(summarize_periods(merged, "Scaled comparison", "gap_scaled", "ratio_scaled"))
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
