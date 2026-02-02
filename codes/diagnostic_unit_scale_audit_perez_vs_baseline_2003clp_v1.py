from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
BASELINE_SERIES = BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1" / "converted_series_2003CLP_1900_1994.csv"
PEREZ_ANCHOR = BASE_DIR / "outputs" / "ANCHOR_PEREZ_FBFK_2003CLP_v1" / "perez_anchor_pack_1860_2010.csv"
PEREZ_METADATA = BASE_DIR / "outputs" / "ANCHOR_PEREZ_FBFK_2003CLP_v1" / "metadata.yaml"
OUTPUT_DIR = BASE_DIR / "outputs" / "DIAGNOSTIC_UNIT_SCALE_AUDIT_v1"

PEREZ_MULTIPLIER_CANDIDATES = [1, 1e3, 1e6]
BASELINE_MULTIPLIER_CANDIDATES = [1, 1e3, 1e6]


def load_metadata(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def compute_stats(series: pd.Series) -> dict[str, float]:
    return {
        "mean": float(series.mean()),
        "p10": float(series.quantile(0.1)),
        "p90": float(series.quantile(0.9)),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(BASELINE_SERIES)
    baseline_total = baseline[baseline["asset"] == "Total"][["year", "I"]].copy()
    baseline_total = baseline_total.rename(columns={"I": "I_baseline"})

    perez = pd.read_csv(PEREZ_ANCHOR)
    perez = perez.rename(columns={"perez_fbfk_total_ex_inv": "I_perez_fbfk"})
    merged = baseline_total.merge(perez[["year", "I_perez_fbfk"]], on="year", how="inner")

    rows = []
    for baseline_mult, perez_mult in product(BASELINE_MULTIPLIER_CANDIDATES, PEREZ_MULTIPLIER_CANDIDATES):
        scaled_baseline = merged["I_baseline"] * baseline_mult
        scaled_perez = merged["I_perez_fbfk"] * perez_mult
        mask = (scaled_baseline > 0) & (scaled_perez > 0)
        if mask.any():
            ratio = scaled_baseline[mask] / scaled_perez[mask]
            logdiff = np.log(scaled_baseline[mask]) - np.log(scaled_perez[mask])
            ratio_stats = compute_stats(ratio)
            logdiff_mean = float(logdiff.mean())
            logdiff_sd = float(logdiff.std())
            n_obs = int(mask.sum())
        else:
            ratio_stats = {"mean": np.nan, "p10": np.nan, "p90": np.nan}
            logdiff_mean = np.nan
            logdiff_sd = np.nan
            n_obs = 0

        score = np.nan
        if np.isfinite(logdiff_mean) and np.isfinite(logdiff_sd):
            score = abs(logdiff_mean) + logdiff_sd

        rows.append(
            {
                "baseline_multiplier": baseline_mult,
                "perez_multiplier": perez_mult,
                "ratio_mean": ratio_stats["mean"],
                "ratio_p10": ratio_stats["p10"],
                "ratio_p90": ratio_stats["p90"],
                "logdiff_mean": logdiff_mean,
                "logdiff_sd": logdiff_sd,
                "n_obs": n_obs,
                "score": score,
            }
        )

    grid = pd.DataFrame(rows).sort_values("score")
    grid.to_csv(OUTPUT_DIR / "scale_grid.csv", index=False)

    best_row = grid.iloc[0].to_dict()
    decision_rule = "minimize abs(logdiff_mean) + logdiff_sd"
    best_payload = {
        "best_pair": {
            "baseline_multiplier": best_row["baseline_multiplier"],
            "perez_multiplier": best_row["perez_multiplier"],
        },
        "score": best_row["score"],
        "decision_rule": decision_rule,
        "n_obs": int(best_row["n_obs"]),
    }
    with (OUTPUT_DIR / "best_scale.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(best_payload, handle, sort_keys=False)

    metadata = load_metadata(PEREZ_METADATA)
    header_note = metadata.get("header_note", "UNKNOWN")
    unit_statement = metadata.get("unit_statement", "UNKNOWN")

    top5 = grid.head(5)
    summary_lines = [
        "# DIAGNOSTIC_UNIT_SCALE_AUDIT_v1 summary",
        "",
        f"Best pair: baseline_multiplier={best_row['baseline_multiplier']}, perez_multiplier={best_row['perez_multiplier']}",
        f"Decision rule: {decision_rule}",
        f"Score: {best_row['score']}",
        "",
        f"Perez header note: {header_note}",
        f"Perez unit statement: {unit_statement}",
        "Baseline unit scale: not explicitly stated in baseline reporting series.",
        "",
        "## Top 5 scale pairs",
    ]
    for _, row in top5.iterrows():
        summary_lines.append(
            f"- baseline {row['baseline_multiplier']} / perez {row['perez_multiplier']} "
            f"(score={row['score']}, ratio_mean={row['ratio_mean']}, logdiff_mean={row['logdiff_mean']}, n_obs={int(row['n_obs'])})"
        )

    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    created_files = [
        OUTPUT_DIR / "scale_grid.csv",
        OUTPUT_DIR / "best_scale.yaml",
        OUTPUT_DIR / "summary.md",
    ]
    print("Created files:")
    for path in created_files:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
