from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import scipy.optimize as opt
from scipy.special import gamma

ASSETS = ["ME", "NRC", "RC"]
AGE_MAX = 150
ADD_TOL = 0.005
PRIORS = {"ME": 15.0, "NRC": 40.0, "RC": 50.0}
OVERLAP_START = 1950
OVERLAP_END = 1994


def ensure_dirs(paths: List[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def load_hofman_investment(raw_dir: Path) -> pd.DataFrame:
    df = pd.read_excel(raw_dir / "Hofman2000_GrossInvestment.xlsx", sheet_name="Gross_Investment_Ig_Hofman2000")
    df = df.rename(
        columns={
            "year": "year",
            "Ig_ME_H2000": "I_ME",
            "Ig_NRC_H2000": "I_NRC",
            "Ig_RC_H2000": "I_RC",
            "Ig_tot_H2000": "I_tot",
        }
    )
    df["I_residual"] = df["I_tot"] - (df["I_ME"] + df["I_NRC"] + df["I_RC"])
    df["s_ME"] = df["I_ME"] / df["I_tot"]
    df["s_NRC"] = df["I_NRC"] / df["I_tot"]
    df["s_RC"] = df["I_RC"] / df["I_tot"]
    df["s_residual"] = df["I_residual"] / df["I_tot"]
    return df


def load_hofman_stocks(raw_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    kg = pd.read_excel(raw_dir / "Hofman_Kstock_gross_net_19501994.xlsx", sheet_name="Kg").rename(columns={"year": "year"})
    kn = pd.read_excel(raw_dir / "Hofman_Kstock_gross_net_19501994.xlsx", sheet_name="Kn").rename(columns={"year": "year"})
    return kg, kn


def to_long(df: pd.DataFrame, value_cols: List[str], var_name: str, value_name: str) -> pd.DataFrame:
    return df.melt(id_vars="year", value_vars=value_cols, var_name=var_name, value_name=value_name)


def overlap_recovery(inv: pd.DataFrame, kg: pd.DataFrame, kn: pd.DataFrame) -> pd.DataFrame:
    inv = inv.set_index("year")
    kg = kg.set_index("year")
    kn = kn.set_index("year")
    years = kg.index
    records = []
    for asset in ASSETS:
        kg_s = kg[asset]
        kn_s = kn[asset]
        delta_kg = kg_s.diff()
        delta_kn = kn_s.diff()
        r_imp = inv.loc[years, f"I_{asset}"] - delta_kg
        d_imp = inv.loc[years, f"I_{asset}"] - delta_kn
        b = kg_s - kn_s
        delta_b = b.diff()
        z = r_imp / kg_s.shift(1)
        delta_rate = d_imp / kn_s.shift(1)
        for y in years:
            records.append(
                {
                    "year": int(y),
                    "asset": asset,
                    "I": inv.loc[y, f"I_{asset}"],
                    "Kg": kg_s.loc[y],
                    "Kn": kn_s.loc[y],
                    "DeltaKg": delta_kg.loc[y],
                    "DeltaKn": delta_kn.loc[y],
                    "R_imp": r_imp.loc[y],
                    "D_imp": d_imp.loc[y],
                    "B": b.loc[y],
                    "DeltaB": delta_b.loc[y],
                    "z": z.loc[y],
                    "delta": delta_rate.loc[y],
                }
            )
    # NR and Total
    nr_records = []
    tot_records = []
    for y in years:
        I_NR = inv.loc[y, "I_ME"] + inv.loc[y, "I_NRC"]
        I_tot = inv.loc[y, "I_tot"]
        kg_nr = kg.loc[y, "ME"] + kg.loc[y, "NRC"]
        kg_tot = kg.loc[y, "Total"]
        kn_nr = kn.loc[y, "ME"] + kn.loc[y, "NRC"]
        kn_tot = kn.loc[y, "Total"]
        delta_kg_nr = kg_nr - (kg.loc[y - 1, "ME"] + kg.loc[y - 1, "NRC"]) if y - 1 in years else np.nan
        delta_kn_nr = kn_nr - (kn.loc[y - 1, "ME"] + kn.loc[y - 1, "NRC"]) if y - 1 in years else np.nan
        delta_kg_tot = kg_tot - kg.loc[y - 1, "Total"] if y - 1 in years else np.nan
        delta_kn_tot = kn_tot - kn.loc[y - 1, "Total"] if y - 1 in years else np.nan
        r_nr = I_NR - delta_kg_nr
        d_nr = I_NR - delta_kn_nr
        r_tot = I_tot - delta_kg_tot
        d_tot = I_tot - delta_kn_tot
        b_nr = kg_nr - kn_nr
        b_tot = kg_tot - kn_tot
        delta_b_nr = b_nr - (
            (kg.loc[y - 1, "ME"] + kg.loc[y - 1, "NRC"]) - (kn.loc[y - 1, "ME"] + kn.loc[y - 1, "NRC"])
        ) if y - 1 in years else np.nan
        delta_b_tot = b_tot - (kg.loc[y - 1, "Total"] - kn.loc[y - 1, "Total"]) if y - 1 in years else np.nan
        z_nr = r_nr / (kg.loc[y - 1, "ME"] + kg.loc[y - 1, "NRC"]) if y - 1 in years else np.nan
        z_tot = r_tot / kg.loc[y - 1, "Total"] if y - 1 in years else np.nan
        delta_nr = d_nr / (kn.loc[y - 1, "ME"] + kn.loc[y - 1, "NRC"]) if y - 1 in years else np.nan
        delta_tot = d_tot / kn.loc[y - 1, "Total"] if y - 1 in years else np.nan
        nr_records.append(
            {
                "year": int(y),
                "asset": "NR",
                "I": I_NR,
                "Kg": kg_nr,
                "Kn": kn_nr,
                "DeltaKg": delta_kg_nr,
                "DeltaKn": delta_kn_nr,
                "R_imp": r_nr,
                "D_imp": d_nr,
                "B": b_nr,
                "DeltaB": delta_b_nr,
                "z": z_nr,
                "delta": delta_nr,
            }
        )
        tot_records.append(
            {
                "year": int(y),
                "asset": "Total",
                "I": I_tot,
                "Kg": kg_tot,
                "Kn": kn_tot,
                "DeltaKg": delta_kg_tot,
                "DeltaKn": delta_kn_tot,
                "R_imp": r_tot,
                "D_imp": d_tot,
                "B": b_tot,
                "DeltaB": delta_b_tot,
                "z": z_tot,
                "delta": delta_tot,
            }
        )
    return pd.DataFrame(records + nr_records + tot_records)


def overlap_audit(df: pd.DataFrame) -> Tuple[str, bool]:
    total_years = len(df[df["asset"] == "Total"])
    total_neg_r = (df[(df["asset"] == "Total") & (df["R_imp"] < 0)]).shape[0]
    total_neg_d = (df[(df["asset"] == "Total") & (df["D_imp"] < 0)]).shape[0]
    share_r = total_neg_r / total_years
    share_d = total_neg_d / total_years
    lines = []
    lines.append(f"Total overlap years: {total_years}")
    lines.append(f"R_imp<0 (Total): {total_neg_r}/{total_years} ({share_r:.3%})")
    lines.append(f"D_imp<0 (Total): {total_neg_d}/{total_years} ({share_d:.3%})")
    stop_flag = share_r > 0.05 or share_d > 0.05
    if stop_flag:
        lines.append("STOP: Hofman-only coherence violated: investigate extraction/year alignment.")
    else:
        lines.append("Hofman-only overlap coherence holds within 5% threshold.")
    return "\n".join(lines), stop_flag


def weibull_survival(scale: float, shape: float, max_age: int) -> np.ndarray:
    ages = np.arange(max_age + 1)
    surv = np.exp(-((ages / scale) ** shape))
    surv[0] = 1.0
    return surv


def rectangular_survival(life: float, max_age: int) -> np.ndarray:
    ages = np.arange(max_age + 1)
    surv = (ages <= life).astype(float)
    surv[0] = 1.0
    return surv


def mean_life_weibull(scale: float, shape: float) -> float:
    return float(scale * gamma(1.0 + 1.0 / shape))


def retirement_from_survival(investment: pd.Series, survival: np.ndarray) -> pd.Series:
    kernel = np.concatenate([[0.0], survival[:-1] - survival[1:]])
    values = np.convolve(investment.values, kernel, mode="full")[: len(investment)]
    return pd.Series(values, index=investment.index)


def stock_from_survival(investment: pd.Series, survival: np.ndarray) -> pd.Series:
    values = np.convolve(investment.values, survival, mode="full")[: len(investment)]
    return pd.Series(values, index=investment.index)


@dataclass
class SurvivalFit:
    asset: str
    family: str
    scale: float
    shape: float
    mean_life: float
    rmse: float
    status: str
    survival: np.ndarray


def fit_survival(asset: str, investment: pd.Series, r_imp: pd.Series, prior: float) -> SurvivalFit:
    positive = r_imp[r_imp >= 0]
    if positive.empty:
        surv = rectangular_survival(prior, AGE_MAX)
        r_model = retirement_from_survival(investment, surv)
        rmse = float(np.sqrt(((r_model.loc[r_imp.index] - r_imp) ** 2).mean()))
        return SurvivalFit(asset, "rectangular", prior, math.inf, prior, rmse, "fallback_non_positive_R", surv)

    years = positive.index

    def objective(params: np.ndarray) -> float:
        scale, shape = params
        surv = weibull_survival(scale, shape, AGE_MAX)
        r_model = retirement_from_survival(investment, surv)
        sse = ((r_model.loc[years] - positive) ** 2).mean()
        mean_life = mean_life_weibull(scale, shape)
        penalty = ((mean_life - prior) / prior) ** 2
        return sse + 0.1 * penalty

    x0 = np.array([prior, 2.0])
    bounds = [(prior * 0.5, prior * 2.5), (0.5, 5.0)]
    try:
        res = opt.minimize(objective, x0=x0, bounds=bounds, method="L-BFGS-B")
    except Exception:
        res = None
    if res is None or not res.success:
        surv = rectangular_survival(prior, AGE_MAX)
        r_model = retirement_from_survival(investment, surv)
        rmse = float(np.sqrt(((r_model.loc[r_imp.index] - r_imp) ** 2).mean()))
        return SurvivalFit(asset, "rectangular", prior, math.inf, prior, rmse, "fallback_opt_failure", surv)

    scale, shape = res.x
    surv = weibull_survival(scale, shape, AGE_MAX)
    r_model = retirement_from_survival(investment, surv)
    rmse = float(np.sqrt(((r_model.loc[r_imp.index] - r_imp) ** 2).mean()))
    mean_life = mean_life_weibull(scale, shape)
    return SurvivalFit(asset, "weibull", float(scale), float(shape), mean_life, rmse, "ok", surv)


def anchor_pre1950_kg(
    investment: pd.Series, survival: np.ndarray, kg_obs_1950: float
) -> Tuple[pd.Series, pd.Series, float]:
    kg_model = stock_from_survival(investment, survival)
    factor = kg_obs_1950 / kg_model.loc[1950]
    kg_model_scaled = kg_model.copy()
    kg_model_scaled.loc[kg_model_scaled.index <= 1949] = kg_model.loc[kg_model.index <= 1949] * factor
    kg_model_scaled.loc[1950] = kg_obs_1950
    delta_kg = kg_model_scaled.diff()
    r_model = investment - delta_kg
    return kg_model_scaled, r_model, factor


def extend_gap_ratio(kg: pd.Series, kn: pd.Series, pre_years: List[int]) -> pd.Series:
    b = kg - kn
    ratio = (b / kg).median()
    b_pre = kg.loc[pre_years] * ratio
    return b_pre


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    raw_dir = base / "data" / "raw"
    out_dir = base / "outputs"
    ensure_dirs([out_dir])

    # Step 1: investment block
    inv_df = load_hofman_investment(raw_dir)
    inv_df.to_csv(out_dir / "investment_block_hofman_1980.csv", index=False)

    # Stocks
    kg_obs, kn_obs = load_hofman_stocks(raw_dir)
    kg_obs = kg_obs.rename(columns={"NR": "NR_obs", "Total": "Total_obs"})
    kn_obs = kn_obs.rename(columns={"NR": "NR_obs", "Total": "Total_obs"})

    # Step 2: overlap recovery
    overlap = overlap_recovery(inv_df, kg_obs[["year", "ME", "NRC", "RC", "Total_obs"]].rename(columns={"Total_obs": "Total"}), kn_obs[["year", "ME", "NRC", "RC", "Total_obs"]].rename(columns={"Total_obs": "Total"}))
    overlap.to_csv(out_dir / "overlap_recovery_1950_1994.csv", index=False)
    audit_text, stop_flag = overlap_audit(overlap)
    (out_dir / "overlap_audit_summary.txt").write_text(audit_text, encoding="utf-8")
    if stop_flag:
        print(audit_text)
        return

    # Step 3: survival fits
    fits: Dict[str, SurvivalFit] = {}
    notes: List[str] = []
    inv_series = inv_df.set_index("year")
    for asset in ASSETS:
        r_series = overlap[overlap["asset"] == asset].set_index("year")["R_imp"]
        fit = fit_survival(asset, inv_series[f"I_{asset}"], r_series, PRIORS[asset])
        fits[asset] = fit
        notes.append(f"{asset}: family={fit.family}, scale={fit.scale}, shape={fit.shape}, mean_life={fit.mean_life}, rmse={fit.rmse}, status={fit.status}")
    pd.DataFrame(
        [
            {
                "asset": a,
                "family": f.family,
                "scale": f.scale,
                "shape": f.shape,
                "mean_life": f.mean_life,
                "rmse": f.rmse,
                "status": f.status,
            }
            for a, f in fits.items()
        ]
    ).to_csv(out_dir / "survival_fit_hofman_1980.csv", index=False)
    (out_dir / "survival_fit_notes.txt").write_text("\n".join(notes), encoding="utf-8")

    # Step 4: reconstruct Kg pre-1950 and anchor
    pre_years = [y for y in inv_df["year"] if 1900 <= y <= 1949]
    kg_pre_records = []
    anchor_notes = []
    kg_series: Dict[str, pd.Series] = {}
    r_series_map: Dict[str, pd.Series] = {}
    for asset in ASSETS:
        inv_asset = inv_series[f"I_{asset}"].loc[1900:1950]
        kg_obs_1950 = float(kg_obs.loc[kg_obs["year"] == 1950, asset].iloc[0])
        kg_model, r_model, factor = anchor_pre1950_kg(inv_asset, fits[asset].survival, kg_obs_1950)
        kg_series[asset] = kg_model
        r_series_map[asset] = r_model
        anchor_notes.append(f"{asset}: anchor_factor={factor}")
        for y in pre_years:
            kg_pre_records.append({"year": int(y), "asset": asset, "Kg_model": kg_model.loc[y], "R_model": r_model.loc[y], "anchor_factor": factor})
    pd.DataFrame(kg_pre_records).to_csv(out_dir / "kg_reconstructed_1900_1949.csv", index=False)
    (out_dir / "kg_anchor_report.txt").write_text("\n".join(anchor_notes), encoding="utf-8")

    # extend kg_series with observed overlap
    for asset in ASSETS:
        kg_series[asset].loc[1950:1994] = kg_obs.set_index("year")[asset].loc[1950:1994]
        r_series_map[asset].loc[1950:1994] = overlap[overlap["asset"] == asset].set_index("year")["R_imp"]

    # Step 5: Kn via gap extension
    kn_series: Dict[str, pd.Series] = {}
    b_series: Dict[str, pd.Series] = {}
    pre_years_list = [y for y in range(1900, 1950)]
    kg_obs_idx = kg_obs.set_index("year")
    kn_obs_idx = kn_obs.set_index("year")
    for asset in ASSETS:
        b_overlap = kg_obs_idx[asset].loc[1950:1994] - kn_obs_idx[asset].loc[1950:1994]
        gap_ratio = (b_overlap / kg_obs_idx[asset].loc[1950:1994]).median()
        kg_pre = kg_series[asset].loc[pre_years_list]
        b_pre = kg_pre * gap_ratio
        kn_pre = kg_pre - b_pre
        kn_full = pd.concat([kn_pre, kn_obs_idx[asset].loc[1950:1994]])
        b_full = pd.concat([b_pre, b_overlap])
        kn_series[asset] = kn_full
        b_series[asset] = b_full

    # Pre-period depreciation
    d_series_map: Dict[str, pd.Series] = {}
    for asset in ASSETS:
        kn_asset = kn_series[asset]
        delta_kn = kn_asset.diff()
        d_series = inv_series[f"I_{asset}"].loc[1900:1994] - delta_kn
        d_series_map[asset] = d_series

    # Compose panels ME/NRC/RC first
    years_full = list(range(1900, 1995))
    records = []
    violations = []
    for y in years_full:
        for asset in ASSETS:
            kg_val = kg_series[asset].loc[y] if y in kg_series[asset].index else np.nan
            kn_val = kn_series[asset].loc[y] if y in kn_series[asset].index else np.nan
            b_val = b_series[asset].loc[y] if y in b_series[asset].index else np.nan
            r_val = r_series_map[asset].loc[y] if y in r_series_map[asset].index else np.nan
            d_val = d_series_map[asset].loc[y] if y in d_series_map[asset].index else np.nan
            I_val = inv_series[f"I_{asset}"].loc[y] if y in inv_series.index else np.nan
            delta_kg_val = kg_val - (kg_series[asset].loc[y - 1] if (y - 1) in kg_series[asset].index else 0)
            delta_kn_val = kn_val - (kn_series[asset].loc[y - 1] if (y - 1) in kn_series[asset].index else 0)
            z_val = r_val / (kg_series[asset].loc[y - 1] if (y - 1) in kg_series[asset].index else np.nan)
            delta_val = d_val / (kn_series[asset].loc[y - 1] if (y - 1) in kn_series[asset].index else np.nan)
            records.append(
                {
                    "year": y,
                    "asset": asset,
                    "I": I_val,
                    "Kg": kg_val,
                    "Kn": kn_val,
                    "B": b_val,
                    "R": r_val,
                    "D": d_val,
                    "DeltaKg": delta_kg_val,
                    "DeltaKn": delta_kn_val,
                    "z": z_val,
                    "delta": delta_val,
                }
            )
            if kg_val < -1e-9 or kn_val < -1e-9 or b_val < -1e-9:
                violations.append(
                    {
                        "year": y,
                        "asset": asset,
                        "type": "admissibility",
                        "message": "negative stock/gap",
                        "value": float(min(kg_val, kn_val, b_val)),
                    }
                )
            if y > 1900 and pd.notna(z_val) and (z_val < 0 or z_val > 1):
                violations.append({"year": y, "asset": asset, "type": "rate", "message": "z outside [0,1]", "value": float(z_val)})
            if y > 1900 and pd.notna(delta_val) and (delta_val < 0 or delta_val > 1):
                violations.append({"year": y, "asset": asset, "type": "rate", "message": "delta outside [0,1]", "value": float(delta_val)})
    panel = pd.DataFrame(records)

    # NR
    nr_records = []
    for y in years_full:
        subset = panel[panel["year"] == y].set_index("asset")
        kg_nr = subset.loc["ME", "Kg"] + subset.loc["NRC", "Kg"]
        kn_nr = subset.loc["ME", "Kn"] + subset.loc["NRC", "Kn"]
        b_nr = subset.loc["ME", "B"] + subset.loc["NRC", "B"]
        I_nr = subset.loc["ME", "I"] + subset.loc["NRC", "I"]
        delta_kg_nr = kg_nr - (
            panel[(panel["year"] == y - 1) & (panel["asset"].isin(["ME", "NRC"]))]["Kg"].sum() if y > 1900 else np.nan
        )
        delta_kn_nr = kn_nr - (
            panel[(panel["year"] == y - 1) & (panel["asset"].isin(["ME", "NRC"]))]["Kn"].sum() if y > 1900 else np.nan
        )
        r_nr = I_nr - delta_kg_nr
        d_nr = I_nr - delta_kn_nr
        z_nr = r_nr / (panel[(panel["year"] == y - 1) & (panel["asset"].isin(["ME", "NRC"]))]["Kg"].sum() if y > 1900 else np.nan)
        delta_nr = d_nr / (panel[(panel["year"] == y - 1) & (panel["asset"].isin(["ME", "NRC"]))]["Kn"].sum() if y > 1900 else np.nan)
        nr_records.append(
            {
                "year": y,
                "asset": "NR",
                "I": I_nr,
                "Kg": kg_nr,
                "Kn": kn_nr,
                "B": b_nr,
                "R": r_nr,
                "D": d_nr,
                "DeltaKg": delta_kg_nr,
                "DeltaKn": delta_kn_nr,
                "z": z_nr,
                "delta": delta_nr,
            }
        )
    nr_panel = pd.DataFrame(nr_records)

    # Total
    total_records = []
    for y in years_full:
        subset = panel[panel["year"] == y].set_index("asset")
        kg_total_pre = subset["Kg"].sum()
        kn_total_pre = subset["Kn"].sum()
        b_total_pre = subset["B"].sum()
        I_total = inv_series["I_tot"].loc[y] if y in inv_series.index else np.nan
        if y >= 1950:
            kg_total = float(kg_obs.loc[kg_obs["year"] == y, "Total_obs"].iloc[0])
            kn_total = float(kn_obs.loc[kn_obs["year"] == y, "Total_obs"].iloc[0])
            b_total = kg_total - kn_total
        else:
            kg_total = kg_total_pre
            kn_total = kn_total_pre
            b_total = b_total_pre
        delta_kg_total = kg_total - (float(kg_obs.loc[kg_obs["year"] == y - 1, "Total_obs"].iloc[0]) if y > 1950 else (panel[panel["year"] == y - 1]["Kg"].sum() if y > 1900 else np.nan))
        delta_kn_total = kn_total - (float(kn_obs.loc[kn_obs["year"] == y - 1, "Total_obs"].iloc[0]) if y > 1950 else (panel[panel["year"] == y - 1]["Kn"].sum() if y > 1900 else np.nan))
        r_total = I_total - delta_kg_total
        d_total = I_total - delta_kn_total
        z_total = r_total / (float(kg_obs.loc[kg_obs["year"] == y - 1, "Total_obs"].iloc[0]) if y > 1950 else (panel[panel["year"] == y - 1]["Kg"].sum() if y > 1900 else np.nan))
        delta_total = d_total / (float(kn_obs.loc[kn_obs["year"] == y - 1, "Total_obs"].iloc[0]) if y > 1950 else (panel[panel["year"] == y - 1]["Kn"].sum() if y > 1900 else np.nan))
        total_records.append(
            {
                "year": y,
                "asset": "Total",
                "I": I_total,
                "Kg": kg_total,
                "Kn": kn_total,
                "B": b_total,
                "R": r_total,
                "D": d_total,
                "DeltaKg": delta_kg_total,
                "DeltaKn": delta_kn_total,
                "z": z_total,
                "delta": delta_total,
                "I_residual": I_total - (subset["I"].sum()),
            }
        )
    tot_panel = pd.DataFrame(total_records)

    combined = pd.concat([panel, nr_panel, tot_panel], ignore_index=True)

    combined.to_csv(out_dir / "harmonized_series_1980CLP_1900_1994.csv", index=False)

    pd.DataFrame(violations).to_csv(out_dir / "violation_log_baseline_1980.csv", index=False)

    # rates file
    combined[["year", "asset", "z", "delta"]].to_csv(out_dir / "rates_1900_1994.csv", index=False)

    # kn reconstruction export pre-1950
    kn_pre_records = []
    for asset in ASSETS:
        for y in pre_years_list:
            kn_pre_records.append({"year": y, "asset": asset, "Kn": kn_series[asset].loc[y], "B": b_series[asset].loc[y]})
    pd.DataFrame(kn_pre_records).to_csv(out_dir / "kn_reconstructed_1900_1949.csv", index=False)

    # audit full summary
    summary_lines = []
    summary_lines.append("Full-period audit 1900-1994")
    summary_lines.append(f"Total records: {len(combined)}")
    z_out = combined[(combined["asset"] == "Total") & ((combined["z"] < 0) | (combined["z"] > 1))].shape[0]
    delta_out = combined[(combined["asset"] == "Total") & ((combined["delta"] < 0) | (combined["delta"] > 1))].shape[0]
    summary_lines.append(f"Total z out-of-bounds count: {z_out}")
    summary_lines.append(f"Total delta out-of-bounds count: {delta_out}")
    (out_dir / "audit_summary_full_1900_1994.txt").write_text("\n".join(summary_lines), encoding="utf-8")
    combined.to_csv(out_dir / "audit_full_1900_1994.csv", index=False)

    # assumptions
    assumptions = {
        "mode": "BASELINE_1980_HOFMAN",
        "investment_source": "Hofman2000_GrossInvestment.xlsx (1980 CLP)",
        "stocks_source": "Hofman_Kstock_gross_net_19501994.xlsx (1980 CLP)",
        "shares_residual": "Ig_residual retained, no forced additivity",
        "survival_family": {a: fits[a].family for a in ASSETS},
        "survival_params": {a: {"scale": fits[a].scale, "shape": fits[a].shape, "mean_life": fits[a].mean_life, "status": fits[a].status} for a in ASSETS},
        "anchor": "Multiplicative factor per asset to match Kg(1950) observed",
        "gap_extension": "Constant B/Kg ratio = median overlap per asset",
    }
    import yaml

    with open(out_dir / "assumptions_baseline_1980.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(assumptions, f, sort_keys=False)

    print("Baseline Hofman 1980 run completed.")


if __name__ == "__main__":
    main()
