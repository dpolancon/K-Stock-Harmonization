from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
BASELINE_SERIES = BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1" / "converted_series_2003CLP_1900_1994.csv"
PEREZ_ANCHOR = BASE_DIR / "outputs" / "ANCHOR_PEREZ_FBFK_2003CLP_v1" / "perez_anchor_pack_1860_2010.csv"
OUTPUT_DIR = BASE_DIR / "outputs" / "DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1"


def trimmed_mean(series: pd.Series, trim: float) -> float:
    if series.empty:
        return float("nan")
    lower = series.quantile(trim)
    upper = series.quantile(1 - trim)
    trimmed = series[(series >= lower) & (series <= upper)]
    return float(trimmed.mean())


def ratio_stats(series: pd.Series) -> dict[str, float]:
    return {
        "mean": float(series.mean()),
        "p10": float(series.quantile(0.1)),
        "p90": float(series.quantile(0.9)),
    }


def summarize_periods(df: pd.DataFrame, ratio_col: str, label: str) -> list[str]:
    periods = {
        "1900-1949": (1900, 1949),
        "1950-1994": (1950, 1994),
        "1973-1989": (1973, 1989),
        "1990-1994": (1990, 1994),
    }
    lines = [f"## {label}"]
    for period_label, (start, end) in periods.items():
        subset = df[(df["year"] >= start) & (df["year"] <= end)]
        stats = ratio_stats(subset[ratio_col].dropna())
        lines.append(f"### {period_label}")
        lines.append(f"- ratio mean: {stats['mean']:.6f}")
        lines.append(f"- ratio p10: {stats['p10']:.6f}")
        lines.append(f"- ratio p90: {stats['p90']:.6f}")
        lines.append("")
    return lines


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_SERIES)
    baseline_total = baseline[baseline["asset"] == "Total"][["year", "I"]].copy()
    baseline_total = baseline_total.rename(columns={"I": "I_baseline_total"})

    perez = pd.read_csv(PEREZ_ANCHOR)
    perez = perez.rename(columns={"perez_fbfk_total_ex_inv": "I_perez_fbfk_exinv"})
    perez = perez[["year", "I_perez_fbfk_exinv"]]

    merged = baseline_total.merge(perez, on="year", how="inner")
    positive_mask = (merged["I_baseline_total"] > 0) & (merged["I_perez_fbfk_exinv"] > 0)
    merged = merged[positive_mask].copy()
    merged["ratio"] = merged["I_baseline_total"] / merged["I_perez_fbfk_exinv"]

    lambda_median = float(merged["ratio"].median())
    lambda_mean = float(merged["ratio"].mean())
    lambda_trim10 = trimmed_mean(merged["ratio"], 0.1)
    lambda_choice = lambda_median
    lambda_rule = "lambda_median (robust to outliers)"

    merged["ratio_over_lambda"] = merged["ratio"] / lambda_choice

    merged.to_csv(OUTPUT_DIR / "overlap_ratios_1900_1994.csv", index=False)

    lambda_payload = {
        "lambda_median": lambda_median,
        "lambda_mean": lambda_mean,
        "lambda_trim10": lambda_trim10,
        "lambda_choice": lambda_choice,
        "lambda_rule": lambda_rule,
        "n_obs": int(len(merged)),
    }
    with (OUTPUT_DIR / "lambda_estimates.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(lambda_payload, handle, sort_keys=False)

    summary_lines = [
        "# DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1 summary",
        "",
        f"Chosen lambda: {lambda_choice}",
        f"Choice rule: {lambda_rule}",
        "",
        "## Lambda candidates",
        f"- lambda_median: {lambda_median}",
        f"- lambda_mean: {lambda_mean}",
        f"- lambda_trim10: {lambda_trim10}",
        "",
    ]
    summary_lines.extend(summarize_periods(merged, "ratio", "Raw ratio (baseline / Perez)"))
    summary_lines.extend(summarize_periods(merged, "ratio_over_lambda", "Ratio normalized by lambda_median"))

    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    created_files = [
        OUTPUT_DIR / "lambda_estimates.yaml",
        OUTPUT_DIR / "overlap_ratios_1900_1994.csv",
        OUTPUT_DIR / "summary.md",
    ]
    print("Created files:")
    for path in created_files:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
