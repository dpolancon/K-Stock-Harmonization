from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
PEREZ_SCALED = (
    BASE_DIR
    / "outputs"
    / "ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED"
    / "perez_anchor_pack_1860_2010_scaled.csv"
)
HOFMAN_SHARES = BASE_DIR / "outputs" / "investment_block_hofman_1980.csv"
BASELINE_SERIES = BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1" / "converted_series_2003CLP_1900_1994.csv"
LAMBDA_SOURCE = BASE_DIR / "outputs" / "DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1" / "lambda_estimates.yaml"

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1"
)

ASSET_MAPPING = {
    "ME": "s_ME",
    "NRC": "s_NRC",
    "RC": "s_RC",
}


def ratio_stats(series: pd.Series) -> dict[str, float]:
    return {
        "mean": float(series.mean()),
        "p10": float(series.quantile(0.1)),
        "p90": float(series.quantile(0.9)),
    }


def logdiff_stats(series: pd.Series) -> dict[str, float]:
    return {
        "mean": float(series.mean()),
        "sd": float(series.std()),
    }


def summarize_periods(df: pd.DataFrame, ratio_col: str, logdiff_col: str) -> list[str]:
    periods = {
        "1900-1949": (1900, 1949),
        "1950-1994": (1950, 1994),
        "1973-1989": (1973, 1989),
        "1990-1994": (1990, 1994),
    }
    lines = []
    for label, (start, end) in periods.items():
        subset = df[(df["year"] >= start) & (df["year"] <= end)]
        ratio_vals = subset[ratio_col].dropna()
        logdiff_vals = subset[logdiff_col].dropna()
        ratio_summary = ratio_stats(ratio_vals)
        logdiff_summary = logdiff_stats(logdiff_vals)
        lines.append(f"### {label}")
        lines.append(f"- ratio mean: {ratio_summary['mean']:.6f}")
        lines.append(f"- ratio p10: {ratio_summary['p10']:.6f}")
        lines.append(f"- ratio p90: {ratio_summary['p90']:.6f}")
        lines.append(f"- logdiff mean: {logdiff_summary['mean']:.6f}")
        lines.append(f"- logdiff sd: {logdiff_summary['sd']:.6f}")
        lines.append("")
    return lines


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    perez = pd.read_csv(PEREZ_SCALED)
    perez = perez.rename(columns={"perez_fbfk_total_ex_inv_scaled": "I_total_candidate"})
    perez = perez[["year", "I_total_candidate"]]
    perez = perez[(perez["year"] >= 1900) & (perez["year"] <= 1994)].copy()

    hofman = pd.read_csv(HOFMAN_SHARES)
    hofman = hofman[(hofman["year"] >= 1900) & (hofman["year"] <= 1994)].copy()

    shares = hofman[["year", *ASSET_MAPPING.values()]].copy()
    shares["share_sum_raw"] = shares[list(ASSET_MAPPING.values())].sum(axis=1)
    for asset, share_col in ASSET_MAPPING.items():
        shares[f"{share_col}_normalized"] = shares[share_col] / shares["share_sum_raw"]

    candidate = perez.merge(shares, on="year", how="left")
    records = []
    for asset, share_col in ASSET_MAPPING.items():
        normalized_col = f"{share_col}_normalized"
        tmp = candidate[["year", "I_total_candidate", normalized_col]].copy()
        tmp["asset"] = asset
        tmp["I_candidate"] = tmp["I_total_candidate"] * tmp[normalized_col]
        tmp["share_used"] = tmp[normalized_col]
        records.append(tmp[["year", "asset", "I_candidate", "I_total_candidate", "share_used"]])

    total_rows = candidate[["year", "I_total_candidate"]].copy()
    total_rows["asset"] = "Total"
    total_rows["I_candidate"] = total_rows["I_total_candidate"]
    total_rows["share_used"] = 1.0
    records.append(total_rows[["year", "asset", "I_candidate", "I_total_candidate", "share_used"]])

    candidate_long = pd.concat(records, ignore_index=True)
    candidate_long["source_total"] = "perez_scaled_exinv"
    candidate_long["source_shares"] = "hofman"
    candidate_long.to_csv(OUTPUT_DIR / "investment_block_candidate_1900_1994.csv", index=False)

    baseline = pd.read_csv(BASELINE_SERIES)
    baseline_total = baseline[baseline["asset"] == "Total"][["year", "I"]].rename(columns={"I": "I_baseline_total"})
    audit = baseline_total.merge(
        candidate_long[candidate_long["asset"] == "Total"][["year", "I_candidate"]],
        on="year",
        how="left",
    )
    audit = audit.rename(columns={"I_candidate": "I_candidate_total"})
    positive_mask = (audit["I_baseline_total"] > 0) & (audit["I_candidate_total"] > 0)
    audit["ratio_baseline_over_candidate"] = np.where(
        positive_mask,
        audit["I_baseline_total"] / audit["I_candidate_total"],
        np.nan,
    )
    audit["logdiff_baseline_minus_candidate"] = np.where(
        positive_mask,
        np.log(audit["I_baseline_total"]) - np.log(audit["I_candidate_total"]),
        np.nan,
    )
    audit.to_csv(OUTPUT_DIR / "audit_candidate_vs_baseline_1900_1994.csv", index=False)

    add_up = candidate_long[candidate_long["asset"] != "Total"].groupby("year")["I_candidate"].sum()
    total_series = candidate_long[candidate_long["asset"] == "Total"].set_index("year")["I_candidate"]
    add_up_diff = (add_up - total_series).abs()
    max_abs_add_up_diff = float(add_up_diff.max())

    negative_count = int((candidate_long["I_candidate"] < 0).sum())
    share_sum_stats = {
        "min": float(shares["share_sum_raw"].min()),
        "mean": float(shares["share_sum_raw"].mean()),
        "max": float(shares["share_sum_raw"].max()),
    }

    summary_lines = [
        "# EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1 summary",
        "",
        "Candidate definition: Perez scaled FBKF ex-inventories (aggregate) split by Hofman asset shares.",
        f"Coverage years: {candidate_long['year'].min()}-{candidate_long['year'].max()}",
        "",
        "## Checks",
        f"- raw share sum (min/mean/max): {share_sum_stats['min']:.6f} / {share_sum_stats['mean']:.6f} / {share_sum_stats['max']:.6f}",
        "- normalized shares sum to 1 by construction",
        f"- negative I_candidate count: {negative_count}",
        f"- add-up max abs diff: {max_abs_add_up_diff:.6f}",
        "",
        "## Baseline vs candidate distance",
    ]
    summary_lines.extend(
        summarize_periods(
            audit,
            "ratio_baseline_over_candidate",
            "logdiff_baseline_minus_candidate",
        )
    )
    summary_lines.append(
        "Interpretation note: this is a candidate investment block for later j-SFC accumulation; it does not alter baseline stocks."
    )
    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    assumptions = {
        "inputs": {
            "perez_scaled_anchor": str(PEREZ_SCALED),
            "hofman_shares": str(HOFMAN_SHARES),
            "baseline_reporting_series": str(BASELINE_SERIES),
        },
        "lambda_source": str(LAMBDA_SOURCE),
        "share_source": str(HOFMAN_SHARES),
        "asset_mapping": ASSET_MAPPING,
        "candidate_total_definition": "Perez FBKF total excl inventories scaled by lambda",
        "notes": "Candidate total excludes inventories by design.",
    }
    with (OUTPUT_DIR / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(assumptions, handle, sort_keys=False)

    created_files = [
        OUTPUT_DIR / "investment_block_candidate_1900_1994.csv",
        OUTPUT_DIR / "audit_candidate_vs_baseline_1900_1994.csv",
        OUTPUT_DIR / "assumptions.yaml",
        OUTPUT_DIR / "summary.md",
    ]
    print("Created files:")
    for path in created_files:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
