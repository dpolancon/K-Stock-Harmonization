from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
INVESTMENT_BLOCK = (
    BASE_DIR
    / "outputs"
    / "EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1"
    / "investment_block_candidate_1900_1994.csv"
)
SURVIVAL_FIT = BASE_DIR / "outputs" / "survival_fit_hofman_1980.csv"
BASELINE_SERIES = BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1" / "converted_series_2003CLP_1900_1994.csv"

OUTPUT_DIR = (
    BASE_DIR
    / "outputs"
    / "EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1"
)

ASSETS = ["ME", "NRC", "RC"]
AGE_MAX = 150
OVERLAP_START = 1950
OVERLAP_END = 1994


def weibull_survival(scale: float, shape: float, max_age: int) -> np.ndarray:
    ages = np.arange(max_age + 1)
    surv = np.exp(-((ages / scale) ** shape))
    surv[0] = 1.0
    return surv


def retirement_from_survival(investment: pd.Series, survival: np.ndarray) -> pd.Series:
    kernel = np.concatenate([[0.0], survival[:-1] - survival[1:]])
    values = np.convolve(investment.values, kernel, mode="full")[: len(investment)]
    return pd.Series(values, index=investment.index)


def stock_from_survival(investment: pd.Series, survival: np.ndarray) -> pd.Series:
    values = np.convolve(investment.values, survival, mode="full")[: len(investment)]
    return pd.Series(values, index=investment.index)


def ratio_stats(series: pd.Series) -> dict[str, float]:
    if series.empty:
        return {"mean": float("nan"), "p10": float("nan"), "p90": float("nan")}
    return {
        "mean": float(series.mean()),
        "p10": float(series.quantile(0.1)),
        "p90": float(series.quantile(0.9)),
    }


def logdiff_stats(series: pd.Series) -> dict[str, float]:
    if series.empty:
        return {"mean": float("nan"), "sd": float("nan")}
    return {
        "mean": float(series.mean()),
        "sd": float(series.std()),
    }


def summarize_periods(df: pd.DataFrame, prefix: str) -> list[str]:
    periods = {
        "1900-1949": (1900, 1949),
        "1950-1994": (1950, 1994),
        "1973-1989": (1973, 1989),
        "1990-1994": (1990, 1994),
    }
    lines = []
    for label, (start, end) in periods.items():
        subset = df[(df["year"] >= start) & (df["year"] <= end)]
        ratio_vals = subset[f"{prefix}_ratio"].dropna()
        logdiff_vals = subset[f"{prefix}_logdiff"].dropna()
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

    investment = pd.read_csv(INVESTMENT_BLOCK)
    investment = investment[investment["asset"].isin(ASSETS)].copy()
    investment = investment.pivot(index="year", columns="asset", values="I_candidate").sort_index()
    investment["Total"] = investment[ASSETS].sum(axis=1)

    survival_fit = pd.read_csv(SURVIVAL_FIT).set_index("asset")
    survival_map = {}
    for asset in ASSETS:
        scale = float(survival_fit.loc[asset, "scale"])
        shape = float(survival_fit.loc[asset, "shape"])
        survival_map[asset] = weibull_survival(scale, shape, AGE_MAX)

    kg_series = {}
    r_series = {}
    for asset in ASSETS:
        surv = survival_map[asset]
        kg_series[asset] = stock_from_survival(investment[asset], surv)
        r_series[asset] = retirement_from_survival(investment[asset], surv)
    kg_series["Total"] = kg_series["ME"] + kg_series["NRC"] + kg_series["RC"]
    r_series["Total"] = r_series["ME"] + r_series["NRC"] + r_series["RC"]

    baseline = pd.read_csv(BASELINE_SERIES)
    baseline = baseline[baseline["asset"].isin(ASSETS)].copy()
    baseline_gap = baseline.set_index(["year", "asset"])["Kg"] - baseline.set_index(["year", "asset"])["Kn"]
    gap_ratios = {}
    for asset in ASSETS:
        gap_ratio = (
            baseline_gap.xs(asset, level="asset")
            / baseline[baseline["asset"] == asset].set_index("year")["Kg"]
        ).dropna()
        early = gap_ratio.loc[gap_ratio.index <= OVERLAP_START + 4].median()
        late = gap_ratio.loc[gap_ratio.index >= OVERLAP_END - 4].median()
        overall = gap_ratio.median()
        if pd.isna(early):
            early = overall
        if pd.isna(late):
            late = overall
        gap_ratios[asset] = {"pre": float(early), "post": float(late)}

    kn_series = {}
    b_series = {}
    years = investment.index
    for asset in ASSETS:
        kg = kg_series[asset]
        gap = pd.Series(index=years, dtype=float)
        pre_mask = kg.index < OVERLAP_START
        post_mask = kg.index > OVERLAP_END
        gap.loc[pre_mask] = kg.loc[pre_mask] * gap_ratios[asset]["pre"]
        gap.loc[post_mask] = kg.loc[post_mask] * gap_ratios[asset]["post"]
        gap.loc[~(pre_mask | post_mask)] = kg.loc[~(pre_mask | post_mask)] * gap_ratios[asset]["post"]
        kn_series[asset] = kg - gap
        b_series[asset] = gap
    kn_series["Total"] = kn_series["ME"] + kn_series["NRC"] + kn_series["RC"]

    records = []
    for asset in ASSETS + ["Total"]:
        df = pd.DataFrame(
            {
                "year": years,
                f"Kg_{asset}": kg_series[asset].values,
                f"Kn_{asset}": kn_series[asset].values,
                f"I_{asset}": investment[asset].values if asset != "Total" else investment["Total"].values,
            }
        )
        records.append(df.set_index("year"))
    combined = pd.concat(records, axis=1).reset_index()
    combined.to_csv(OUTPUT_DIR / "candidate_stocks_1900_1994.csv", index=False)

    audit_rows = []
    for asset in ASSETS + ["Total"]:
        kg = kg_series[asset]
        kn = kn_series[asset]
        invest = investment[asset] if asset != "Total" else investment["Total"]
        r = r_series[asset]
        delta_kg = kg.diff()
        delta_kn = kn.diff()
        residual_kg = delta_kg - (invest - r)
        d_imp = invest - delta_kn
        delta_rate = d_imp / kn.shift(1)
        z_rate = r / kg.shift(1)
        audit_rows.append(
            pd.DataFrame(
                {
                    "year": years,
                    "asset": asset,
                    "Kg": kg.values,
                    "Kn": kn.values,
                    "I": invest.values,
                    "R": r.values,
                    "DeltaKg": delta_kg.values,
                    "DeltaKn": delta_kn.values,
                    "residual_kg": residual_kg.values,
                    "z_rate": z_rate.values,
                    "delta_rate": delta_rate.values,
                }
            )
        )
    audit = pd.concat(audit_rows, ignore_index=True)
    audit["negative_Kg"] = audit["Kg"] < 0
    audit["negative_Kn"] = audit["Kn"] < 0
    audit.to_csv(OUTPUT_DIR / "candidate_audit_1900_1994.csv", index=False)

    baseline_totals = pd.read_csv(BASELINE_SERIES)
    baseline_totals = baseline_totals[baseline_totals["asset"].isin(ASSETS + ["Total"])]
    baseline_totals = baseline_totals.pivot(index="year", columns="asset", values=["Kg", "Kn"])
    baseline_totals.columns = [f"baseline_{col[0]}_{col[1]}" for col in baseline_totals.columns]
    baseline_totals = baseline_totals.reset_index()

    distance = combined.reset_index().merge(baseline_totals, on="year", how="left")
    for asset in ASSETS + ["Total"]:
        candidate_kg = distance[f"Kg_{asset}"]
        baseline_kg = distance[f"baseline_Kg_{asset}"]
        candidate_kn = distance[f"Kn_{asset}"]
        baseline_kn = distance[f"baseline_Kn_{asset}"]
        positive_kg = (baseline_kg > 0) & (candidate_kg > 0)
        positive_kn = (baseline_kn > 0) & (candidate_kn > 0)
        distance[f"Kg_ratio_{asset}"] = np.where(positive_kg, baseline_kg / candidate_kg, np.nan)
        distance[f"Kn_ratio_{asset}"] = np.where(positive_kn, baseline_kn / candidate_kn, np.nan)
        distance[f"Kg_logdiff_{asset}"] = np.where(
            positive_kg, np.log(baseline_kg) - np.log(candidate_kg), np.nan
        )
        distance[f"Kn_logdiff_{asset}"] = np.where(
            positive_kn, np.log(baseline_kn) - np.log(candidate_kn), np.nan
        )

    distance_summary = distance[
        [
            "year",
            "Kg_ME",
            "Kg_NRC",
            "Kg_RC",
            "Kg_Total",
            "Kn_ME",
            "Kn_NRC",
            "Kn_RC",
            "Kn_Total",
            "baseline_Kg_ME",
            "baseline_Kg_NRC",
            "baseline_Kg_RC",
            "baseline_Kg_Total",
            "baseline_Kn_ME",
            "baseline_Kn_NRC",
            "baseline_Kn_RC",
            "baseline_Kn_Total",
            "Kg_ratio_ME",
            "Kg_ratio_NRC",
            "Kg_ratio_RC",
            "Kg_ratio_Total",
            "Kn_ratio_ME",
            "Kn_ratio_NRC",
            "Kn_ratio_RC",
            "Kn_ratio_Total",
            "Kg_logdiff_ME",
            "Kg_logdiff_NRC",
            "Kg_logdiff_RC",
            "Kg_logdiff_Total",
            "Kn_logdiff_ME",
            "Kn_logdiff_NRC",
            "Kn_logdiff_RC",
            "Kn_logdiff_Total",
        ]
    ].copy()
    distance_summary["Kg_ratio"] = distance_summary["Kg_ratio_Total"]
    distance_summary["Kn_ratio"] = distance_summary["Kn_ratio_Total"]
    distance_summary["Kg_logdiff"] = distance_summary["Kg_logdiff_Total"]
    distance_summary["Kn_logdiff"] = distance_summary["Kn_logdiff_Total"]
    distance_summary.to_csv(
        OUTPUT_DIR / "candidate_vs_baseline_stock_distance_1900_1994.csv", index=False
    )

    negatives = audit.groupby("asset")[["negative_Kg", "negative_Kn"]].sum().astype(int)
    min_values = audit.groupby("asset")[["Kg", "Kn"]].min()
    combined_indexed = combined.set_index("year")
    kg_sum = combined_indexed[["Kg_ME", "Kg_NRC", "Kg_RC"]].sum(axis=1)
    kn_sum = combined_indexed[["Kn_ME", "Kn_NRC", "Kn_RC"]].sum(axis=1)
    add_up_diff = pd.DataFrame(
        {
            "Kg_diff": combined_indexed["Kg_Total"] - kg_sum,
            "Kn_diff": combined_indexed["Kn_Total"] - kn_sum,
        }
    )
    max_add_up = add_up_diff.abs().max().to_dict()

    residual_max = audit["residual_kg"].abs().max()

    summary_lines = [
        "# EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1 summary",
        "",
        "Candidate definition: stocks accumulated from Perez-scaled FBKF ex-inventories totals split by Hofman shares, using baseline survival parameters.",
        f"Coverage years: {combined['year'].min()}-{combined['year'].max()}",
        "",
        "## Core validity checks",
    ]
    for asset in ASSETS + ["Total"]:
        summary_lines.append(
            f"- negatives ({asset}): Kg={negatives.loc[asset, 'negative_Kg']}, Kn={negatives.loc[asset, 'negative_Kn']}"
        )
        summary_lines.append(
            f"- min values ({asset}): Kg={min_values.loc[asset, 'Kg']:.6f}, Kn={min_values.loc[asset, 'Kn']:.6f}"
        )
    summary_lines.extend(
        [
            f"- add-up max abs diff: Kg={max_add_up['Kg_diff']:.6f}, Kn={max_add_up['Kn_diff']:.6f}",
            f"- max abs residual (Kg identity): {residual_max:.6f}",
            "",
            "## Distance vs baseline (Total)",
        ]
    )
    summary_lines.append("### Kg_Total (baseline/candidate)")
    summary_lines.extend(summarize_periods(distance_summary, "Kg"))
    summary_lines.append("### Kn_Total (baseline/candidate)")
    summary_lines.extend(summarize_periods(distance_summary, "Kn"))
    summary_lines.append(
        "Interpretation note: This is a candidate reconstruction for evaluating the Perez-mother investment path under the j-SFC stock-flow closure; it is not yet a replacement baseline."
    )
    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    assumptions = {
        "inputs": {
            "investment_block_candidate": str(INVESTMENT_BLOCK),
            "survival_fit": str(SURVIVAL_FIT),
            "baseline_reporting_series": str(BASELINE_SERIES),
        },
        "notes": "candidate stocks computed from candidate investment block; baseline untouched",
        "inventories_excluded": True,
        "engine_reference": "weibull survival + stock_from_survival from codes/run_harmonization.py",
    }
    with (OUTPUT_DIR / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(assumptions, handle, sort_keys=False)

    created_files = [
        OUTPUT_DIR / "candidate_stocks_1900_1994.csv",
        OUTPUT_DIR / "candidate_audit_1900_1994.csv",
        OUTPUT_DIR / "candidate_vs_baseline_stock_distance_1900_1994.csv",
        OUTPUT_DIR / "assumptions.yaml",
        OUTPUT_DIR / "summary.md",
    ]
    print("Created files:")
    for path in created_files:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
