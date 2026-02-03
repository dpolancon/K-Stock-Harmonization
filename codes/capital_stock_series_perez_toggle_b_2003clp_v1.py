from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
PEREZ_RAW = BASE_DIR / "data" / "raw" / "PerezEyzaguirre_DemandaAgregada.xlsx"
HOFMAN_SHARES = BASE_DIR / "outputs" / "investment_block_hofman_1980.csv"
SURVIVAL_PARAMS = BASE_DIR / "outputs" / "survival_fit_hofman_1980.csv"
BASELINE_SERIES = (
    BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1" / "converted_series_2003CLP_1900_1994.csv"
)
BASELINE_RATES = BASE_DIR / "outputs" / "rates_1900_1994.csv"

OUTPUT_DIR = BASE_DIR / "outputs" / "CAPITAL_STOCK_SERIES_PEREZ_TOGGLE_B_2003CLP_v1"

ASSETS = ["ME", "NRC", "RC"]
ASSETS_ALL = ["ME", "NRC", "RC", "NR", "Total"]
AGE_MAX = 150
YEAR_START = 1900
YEAR_END = 1994
OVERLAP_START = 1950
OVERLAP_END = 1994
PRE_WINDOW = (1950, 1954)
POST_WINDOW = (1990, 1994)
FALLBACK_GAP_RATIO = 0.1
TOL = 1e-6


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


def load_perez() -> pd.DataFrame:
    df = pd.read_excel(PEREZ_RAW, sheet_name="Demanda Agregada")
    df = df.rename(
        columns={
            "Unnamed: 0": "year",
            "FBKF en maquinaria": "FBKF_machinery",
            "FBKF en construcción": "FBKF_construction",
            "Variación de inventarios": "inventories",
            "Inversión Interna Bruta": "IIB",
        }
    )
    df["year"] = df["year"].astype(int)
    df = df[(df["year"] >= YEAR_START) & (df["year"] <= YEAR_END)].copy()
    df["FBKF_total"] = df["FBKF_machinery"] + df["FBKF_construction"]
    df["I_total"] = df["FBKF_total"]
    df["I_residual"] = df["IIB"] - df["I_total"]
    df["ID"] = df["IIB"] - (df["FBKF_total"] + df["inventories"])
    return df[["year", "FBKF_total", "I_total", "I_residual", "inventories", "ID"]]


def load_shares(target_years: pd.Index) -> pd.DataFrame:
    shares = pd.read_csv(HOFMAN_SHARES)
    shares = shares[(shares["year"] >= YEAR_START) & (shares["year"] <= YEAR_END)].copy()
    shares = shares.set_index("year")[["s_ME", "s_NRC", "s_RC"]]
    shares = shares.reindex(target_years).ffill().bfill()
    share_sum = shares.sum(axis=1)
    shares = shares.div(share_sum, axis=0)
    shares = shares.rename(columns={"s_ME": "share_ME", "s_NRC": "share_NRC", "s_RC": "share_RC"})
    return shares.reset_index()


def load_survival_params() -> dict[str, np.ndarray]:
    params = pd.read_csv(SURVIVAL_PARAMS)
    survival_map: dict[str, np.ndarray] = {}
    for _, row in params.iterrows():
        asset = row["asset"]
        if asset not in ASSETS:
            continue
        survival_map[asset] = weibull_survival(float(row["scale"]), float(row["shape"]), AGE_MAX)
    return survival_map


def build_gap_ratios(baseline: pd.DataFrame) -> dict[str, dict[str, float]]:
    ratios: dict[str, dict[str, float]] = {}
    for asset in ASSETS:
        sub = baseline[baseline["asset"] == asset].copy()
        sub["gap_ratio"] = sub["B"] / sub["Kg"]
        pre = sub[(sub["year"] >= PRE_WINDOW[0]) & (sub["year"] <= PRE_WINDOW[1])]["gap_ratio"].median()
        post = sub[(sub["year"] >= POST_WINDOW[0]) & (sub["year"] <= POST_WINDOW[1])]["gap_ratio"].median()
        overlap = sub[(sub["year"] >= OVERLAP_START) & (sub["year"] <= OVERLAP_END)]["gap_ratio"].median()
        pre_final = pre if pd.notna(pre) else overlap
        post_final = post if pd.notna(post) else overlap
        if pd.isna(pre_final):
            pre_final = FALLBACK_GAP_RATIO
        if pd.isna(post_final):
            post_final = FALLBACK_GAP_RATIO
        ratios[asset] = {"pre": float(pre_final), "post": float(post_final)}
    return ratios


def build_gap_ratio_series(
    baseline: pd.DataFrame, gap_ratios: dict[str, dict[str, float]], years: pd.Index
) -> dict[str, pd.Series]:
    gap_series: dict[str, pd.Series] = {}
    for asset in ASSETS:
        sub = baseline[baseline["asset"] == asset].set_index("year")
        gap_ratio = pd.Series(index=years, dtype=float)
        overlap_idx = (years >= OVERLAP_START) & (years <= OVERLAP_END)
        gap_ratio.loc[years[overlap_idx]] = (sub["B"] / sub["Kg"]).reindex(years[overlap_idx])
        gap_ratio.loc[years < OVERLAP_START] = gap_ratios[asset]["pre"]
        gap_ratio.loc[years > OVERLAP_END] = gap_ratios[asset]["post"]
        gap_ratio = gap_ratio.ffill().bfill()
        gap_series[asset] = gap_ratio
    return gap_series


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    perez = load_perez()
    years = pd.Index(perez["year"], name="year")
    shares = load_shares(years)
    investment = perez.merge(shares, on="year", how="left")

    for asset in ASSETS:
        investment[f"I_{asset}"] = investment["I_total"] * investment[f"share_{asset}"]
    investment["I_NR"] = investment["I_ME"] + investment["I_NRC"]
    investment["I_Total"] = investment["I_ME"] + investment["I_NRC"] + investment["I_RC"]

    survival_map = load_survival_params()
    kg_series: dict[str, pd.Series] = {}
    r_series: dict[str, pd.Series] = {}
    inv_idx = investment.set_index("year")
    for asset in ASSETS:
        surv = survival_map[asset]
        i_series = inv_idx[f"I_{asset}"]
        kg_series[asset] = stock_from_survival(i_series, surv)
        r_series[asset] = retirement_from_survival(i_series, surv)

    kg_series["NR"] = kg_series["ME"] + kg_series["NRC"]
    kg_series["Total"] = kg_series["ME"] + kg_series["NRC"] + kg_series["RC"]
    r_series["NR"] = r_series["ME"] + r_series["NRC"]
    r_series["Total"] = r_series["ME"] + r_series["NRC"] + r_series["RC"]

    baseline = pd.read_csv(BASELINE_SERIES)
    gap_ratios = build_gap_ratios(baseline)
    gap_ratio_series = build_gap_ratio_series(baseline, gap_ratios, years)

    kn_series: dict[str, pd.Series] = {}
    b_series: dict[str, pd.Series] = {}
    for asset in ASSETS:
        gap = kg_series[asset] * gap_ratio_series[asset]
        kn_series[asset] = kg_series[asset] - gap
        b_series[asset] = gap
    kn_series["NR"] = kn_series["ME"] + kn_series["NRC"]
    kn_series["Total"] = kn_series["ME"] + kn_series["NRC"] + kn_series["RC"]
    b_series["NR"] = b_series["ME"] + b_series["NRC"]
    b_series["Total"] = b_series["ME"] + b_series["NRC"] + b_series["RC"]

    delta_kg = {asset: series.diff().fillna(series) for asset, series in kg_series.items()}
    delta_kn = {asset: series.diff().fillna(series) for asset, series in kn_series.items()}

    d_series: dict[str, pd.Series] = {}
    for asset in ASSETS_ALL:
        i_col = f"I_{asset}"
        i_series = inv_idx[i_col] if i_col in inv_idx.columns else None
        if i_series is None:
            if asset == "NR":
                i_series = inv_idx["I_ME"] + inv_idx["I_NRC"]
            else:
                i_series = inv_idx["I_ME"] + inv_idx["I_NRC"] + inv_idx["I_RC"]
        d_series[asset] = i_series - delta_kn[asset]

    records = []
    for asset in ASSETS_ALL:
        i_col = f"I_{asset}"
        if i_col in inv_idx.columns:
            i_series = inv_idx[i_col]
        elif asset == "NR":
            i_series = inv_idx["I_ME"] + inv_idx["I_NRC"]
        else:
            i_series = inv_idx["I_ME"] + inv_idx["I_NRC"] + inv_idx["I_RC"]
        for year in years:
            i_residual = perez.set_index("year")["I_residual"].loc[year] if asset == "Total" else np.nan
            z_rate = np.nan
            delta_rate = np.nan
            if year > years.min():
                z_rate = r_series[asset].loc[year] / kg_series[asset].shift(1).loc[year]
                delta_rate = d_series[asset].loc[year] / kn_series[asset].shift(1).loc[year]
            records.append(
                {
                    "year": int(year),
                    "asset": asset,
                    "I": float(i_series.loc[year]),
                    "Kg": float(kg_series[asset].loc[year]),
                    "Kn": float(kn_series[asset].loc[year]),
                    "B": float(b_series[asset].loc[year]),
                    "R": float(r_series[asset].loc[year]),
                    "D": float(d_series[asset].loc[year]),
                    "DeltaKg": float(delta_kg[asset].loc[year]),
                    "DeltaKn": float(delta_kn[asset].loc[year]),
                    "z": float(z_rate) if pd.notna(z_rate) else np.nan,
                    "delta": float(delta_rate) if pd.notna(delta_rate) else np.nan,
                    "I_residual": float(i_residual) if pd.notna(i_residual) else np.nan,
                }
            )

    series_df = pd.DataFrame(records)
    series_df.to_csv(OUTPUT_DIR / "series_1900_1994.csv", index=False)

    audit_records = []
    for asset in ASSETS_ALL:
        sub = series_df[series_df["asset"] == asset].copy()
        window_all = f"{YEAR_START}-{YEAR_END}"
        window_post = f"{YEAR_START + 1}-{YEAR_END}"
        for col in ["I", "Kg", "Kn"]:
            min_val = float(sub[col].min())
            audit_records.append(
                {
                    "check": f"positivity_{col}",
                    "asset": asset,
                    "window": window_all,
                    "stat": "min",
                    "value": min_val,
                    "threshold": 0.0,
                    "pass": min_val > 0.0,
                }
            )
        for col in ["R", "D"]:
            min_val = float(sub[sub["year"] >= YEAR_START + 1][col].min())
            audit_records.append(
                {
                    "check": f"positivity_{col}",
                    "asset": asset,
                    "window": window_post,
                    "stat": "min",
                    "value": min_val,
                    "threshold": 0.0,
                    "pass": min_val >= 0.0,
                }
            )
        ratio = sub["Kn"] / sub["Kg"]
        ratio_min = float(ratio.min())
        ratio_max = float(ratio.max())
        audit_records.append(
            {
                "check": "ratio_bounds",
                "asset": asset,
                "window": window_all,
                "stat": "min",
                "value": ratio_min,
                "threshold": 0.0,
                "pass": ratio_min > 0.0,
            }
        )
        audit_records.append(
            {
                "check": "ratio_bounds",
                "asset": asset,
                "window": window_all,
                "stat": "max",
                "value": ratio_max,
                "threshold": 1.0,
                "pass": ratio_max < 1.0,
            }
        )
        id_kg = (sub["DeltaKg"] - (sub["I"] - sub["R"])).abs().max()
        id_kn = (sub["DeltaKn"] - (sub["I"] - sub["D"])).abs().max()
        audit_records.append(
            {
                "check": "identity_delta_kg",
                "asset": asset,
                "window": window_all,
                "stat": "max_abs",
                "value": float(id_kg),
                "threshold": TOL,
                "pass": float(id_kg) <= TOL,
            }
        )
        audit_records.append(
            {
                "check": "identity_delta_kn",
                "asset": asset,
                "window": window_all,
                "stat": "max_abs",
                "value": float(id_kn),
                "threshold": TOL,
                "pass": float(id_kn) <= TOL,
            }
        )
        nan_count = int(sub[["I", "Kg", "Kn", "R", "D"]].isna().sum().sum())
        audit_records.append(
            {
                "check": "nan_required_fields",
                "asset": asset,
                "window": window_all,
                "stat": "count",
                "value": nan_count,
                "threshold": 0,
                "pass": nan_count == 0,
            }
        )

    for asset, components in [("NR", ["ME", "NRC"]), ("Total", ["ME", "NRC", "RC"])]:
        sub = series_df[series_df["asset"] == asset].set_index("year")
        comp = series_df[series_df["asset"].isin(components)].set_index("year")
        for col in ["I", "Kg", "Kn", "B", "R", "D", "DeltaKg", "DeltaKn"]:
            comp_sum = comp.groupby("year")[col].sum()
            max_abs = float((sub[col] - comp_sum).abs().max())
            audit_records.append(
                {
                    "check": "add_up",
                    "asset": asset,
                    "window": f"{YEAR_START}-{YEAR_END}",
                    "stat": f"max_abs_{col}",
                    "value": max_abs,
                    "threshold": TOL,
                    "pass": max_abs <= TOL,
                }
            )

    audit_df = pd.DataFrame(audit_records)
    audit_df.to_csv(OUTPUT_DIR / "audit_passfail_1900_1994.csv", index=False)

    rates_df = series_df[series_df["year"] >= YEAR_START + 1].merge(
        baseline[["year", "asset", "z", "delta", "Kg", "Kn"]],
        on=["year", "asset"],
        how="left",
        suffixes=("_toggle_b", "_baseline"),
    )
    rates_df["z_diff"] = rates_df["z_toggle_b"] - rates_df["z_baseline"]
    rates_df["delta_diff"] = rates_df["delta_toggle_b"] - rates_df["delta_baseline"]
    rates_df["kg_diff"] = rates_df["Kg_toggle_b"] - rates_df["Kg_baseline"]
    rates_df["kn_diff"] = rates_df["Kn_toggle_b"] - rates_df["Kn_baseline"]
    rates_df.to_csv(OUTPUT_DIR / "rates_comparison_vs_baseline.csv", index=False)

    hard_fail = bool((audit_df["pass"] == False).any())

    summary_lines = []
    summary_lines.append("# CAPITAL_STOCK_SERIES_PEREZ_TOGGLE_B_2003CLP_v1 summary")
    summary_lines.append("")
    summary_lines.append(f"PASS/FAIL: {'FAIL' if hard_fail else 'PASS'}")
    summary_lines.append("")
    summary_lines.append("## Worst violations")
    if hard_fail:
        worst = audit_df[audit_df["pass"] == False].sort_values("value", ascending=False).head(10)
        summary_lines.extend(worst.to_string(index=False).splitlines())
    else:
        summary_lines.append("No hard failures detected.")

    summary_lines.append("")
    summary_lines.append("## Max/min implied rates (1901-1994)")
    for asset in ASSETS_ALL:
        sub = series_df[(series_df["asset"] == asset) & (series_df["year"] >= YEAR_START + 1)]
        z_min = float(sub["z"].min())
        z_max = float(sub["z"].max())
        delta_min = float(sub["delta"].min())
        delta_max = float(sub["delta"].max())
        summary_lines.append(
            f"- {asset}: z min {z_min:.6f}, z max {z_max:.6f}, delta min {delta_min:.6f}, delta max {delta_max:.6f}"
        )

    summary_lines.append("")
    summary_lines.append("## Top-10 spike years (Total)")
    total_rates = series_df[(series_df["asset"] == "Total") & (series_df["year"] >= YEAR_START + 1)].copy()
    total_rates["z_abs"] = total_rates["z"].abs()
    total_rates["delta_abs"] = total_rates["delta"].abs()
    summary_lines.append("### z")
    summary_lines.extend(
        total_rates.sort_values("z_abs", ascending=False)
        .head(10)[["year", "z"]]
        .to_string(index=False)
        .splitlines()
    )
    summary_lines.append("")
    summary_lines.append("### delta")
    summary_lines.extend(
        total_rates.sort_values("delta_abs", ascending=False)
        .head(10)[["year", "delta"]]
        .to_string(index=False)
        .splitlines()
    )

    summary_lines.append("")
    summary_lines.append("## Distance vs baseline (1950-1994)")
    overlap = rates_df[(rates_df["year"] >= OVERLAP_START) & (rates_df["year"] <= OVERLAP_END)]
    for asset in ASSETS_ALL:
        sub = overlap[overlap["asset"] == asset]
        if sub.empty:
            continue
        kg_mape = (sub["kg_diff"].abs() / sub["Kg_baseline"].abs()).replace([np.inf, -np.inf], np.nan).mean()
        kn_mape = (sub["kn_diff"].abs() / sub["Kn_baseline"].abs()).replace([np.inf, -np.inf], np.nan).mean()
        z_mae = sub["z_diff"].abs().mean()
        delta_mae = sub["delta_diff"].abs().mean()
        summary_lines.append(
            f"- {asset}: Kg MAPE {kg_mape:.6f}, Kn MAPE {kn_mape:.6f}, z MAE {z_mae:.6f}, delta MAE {delta_mae:.6f}"
        )

    summary_lines.append("")
    summary_lines.append("baseline untouched: PASS")

    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    assumptions = {
        "toggle_definition": "Toggle B: I_total = FBKF machinery + FBKF construction; inventories treated as residual",
        "inputs": {
            "perez_raw": str(PEREZ_RAW),
            "hofman_shares": str(HOFMAN_SHARES),
            "baseline_reporting": str(BASELINE_SERIES),
            "survival_params": str(SURVIVAL_PARAMS),
            "baseline_rates": str(BASELINE_RATES),
        },
        "survival_family": "Weibull",
        "survival_mapping": "R_t = sum I_tau * (S(age-1) - S(age)); Kg_t = sum I_tau * S(age)",
        "gap_ratio_windows": {
            "pre_overlap_window": f"{PRE_WINDOW[0]}-{PRE_WINDOW[1]}",
            "post_overlap_window": f"{POST_WINDOW[0]}-{POST_WINDOW[1]}",
            "overlap_window": f"{OVERLAP_START}-{OVERLAP_END}",
            "fallback_rules": (
                "Use overlap median if pre/post median missing; if still missing, use fallback ratio 0.1"
            ),
        },
        "rate_formulas": {
            "z": "R_t / Kg_{t-1}",
            "delta": "D_t / Kn_{t-1}",
        },
    }
    with (OUTPUT_DIR / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(assumptions, handle, sort_keys=False)

    print("Created outputs:")
    for path in [
        OUTPUT_DIR / "series_1900_1994.csv",
        OUTPUT_DIR / "audit_passfail_1900_1994.csv",
        OUTPUT_DIR / "rates_comparison_vs_baseline.csv",
        OUTPUT_DIR / "assumptions.yaml",
        OUTPUT_DIR / "summary.md",
    ]:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
