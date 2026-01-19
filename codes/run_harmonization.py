from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import scipy.optimize as opt
from scipy.special import gamma
import yaml


ASSETS = ["ME", "NRC", "RC"]
ASSET_PRIORS = {"ME": 15.0, "NRC": 40.0, "RC": 50.0}
OVERLAP_START = 1950
OVERLAP_END = 1994
ADDITIVITY_TOL = 0.005  # 0.5%
AGE_MAX = 150
LAMBDA_FALLBACK = 0.247


@dataclass
class SurvivalResult:
    asset: str
    scale: float
    shape: float
    mean_life: float
    rmse: float
    survival: pd.Series  # indexed by age
    retirements_model: pd.Series  # indexed by year


class ViolationLog:
    def __init__(self) -> None:
        self.records: List[Dict] = []

    def add(self, vtype: str, asset: str, year: int, message: str, value) -> None:
        self.records.append(
            {"type": vtype, "asset": asset, "year": int(year), "message": message, "value": float(value) if pd.notna(value) else None}
        )

    def to_frame(self) -> pd.DataFrame:
        if not self.records:
            return pd.DataFrame(columns=["type", "asset", "year", "message", "value"])
        return pd.DataFrame(self.records)


def ensure_dirs(paths: Iterable[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def compute_deflator(anchor_path: Path) -> float:
    kg_anchor = pd.read_excel(anchor_path, sheet_name="Hofman_2000_1950_anchors_Kg")
    kg_1980 = kg_anchor[kg_anchor["prices"] == 1980].iloc[0]
    kg_2003 = kg_anchor[kg_anchor["prices"] == 2003].iloc[0]
    ratio = (kg_2003["Kg_ME_H2000"] * 1000) / kg_1980["Kg_ME_H2000"]
    return float(ratio)


def load_perez(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Demanda Agregada")
    col_year = df.columns[0]
    col_total = next(c for c in df.columns if "Invers" in c)
    df = df.rename(columns={col_year: "year", col_total: "I_tot_control"})
    df["year"] = df["year"].astype(int)
    df = df[["year", "I_tot_control"]].copy()
    return df


def load_lambda_bar(base_dir: Path) -> Tuple[float, str]:
    lambda_path = base_dir / "data" / "diagnostics" / "overlap_investment_ratio_lambda.csv"
    if lambda_path.exists():
        lambda_df = pd.read_csv(lambda_path)
        source_col = None
        if "lambda" in lambda_df.columns:
            source_col = "lambda"
        elif "lambda_ratio" in lambda_df.columns:
            source_col = "lambda_ratio"
        if source_col:
            lambda_bar = float(lambda_df[source_col].mean())
            source = f"mean({source_col}) from overlap_investment_ratio_lambda.csv"
            return lambda_bar, source
    # fallback
    return float(LAMBDA_FALLBACK), "fallback constant 0.247"


def load_hofman_shares(path: Path, log: ViolationLog) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Gross_Investment_Ig_Hofman2000")
    df = df.rename(
        columns={
            "Ig_ME_H2000": "I_ME",
            "Ig_NRC_H2000": "I_NRC",
            "Ig_RC_H2000": "I_RC",
            "Ig_tot_H2000": "I_tot",
        }
    )
    df["year"] = df["year"].astype(int)
    df["I_NR"] = df["I_ME"] + df["I_NRC"]
    df["I_sum_components"] = df["I_ME"] + df["I_NRC"] + df["I_RC"]
    df["share_ME"] = df["I_ME"] / df["I_tot"]
    df["share_NRC"] = df["I_NRC"] / df["I_tot"]
    df["share_RC"] = df["I_RC"] / df["I_tot"]
    df["share_NR"] = df["share_ME"] + df["share_NRC"]

    mismatch = (df["I_sum_components"] - df["I_tot"]) / df["I_tot"]
    for idx, rel in mismatch[mismatch.abs() > ADDITIVITY_TOL].items():
        log.add(
            "definitional mismatch",
            "Total",
            int(df.loc[idx, "year"]),
            "Hofman investment components deviate from total",
            rel,
        )
    shares = df[["year", "share_ME", "share_NRC", "share_RC", "share_NR"]].copy()
    return shares


def extend_shares(shares: pd.DataFrame, target_years: pd.Index) -> pd.DataFrame:
    shares = shares.set_index("year").reindex(target_years)
    shares = shares.ffill().bfill()
    return shares


def split_investment(control: pd.DataFrame, shares: pd.DataFrame, log: ViolationLog) -> pd.DataFrame:
    df = control.set_index("year").join(shares, how="left")
    for col in ["share_ME", "share_NRC", "share_RC"]:
        df[col] = df[col].ffill().bfill()
    df["I_ME"] = df["I_tot_control"] * df["share_ME"]
    df["I_NRC"] = df["I_tot_control"] * df["share_NRC"]
    df["I_RC"] = df["I_tot_control"] * df["share_RC"]
    df["I_NR"] = df["I_ME"] + df["I_NRC"]
    df["I_Total"] = df["I_ME"] + df["I_NRC"] + df["I_RC"]

    rel = (df["I_Total"] - df["I_tot_control"]) / df["I_tot_control"]
    for year, val in rel[rel.abs() > ADDITIVITY_TOL].items():
        log.add("definitional mismatch", "Total", int(year), "Split investment does not add to control total", val)
    return df.reset_index()


def load_hofman_stocks(path: Path, deflator: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    kg = pd.read_excel(path, sheet_name="Kg")
    kn = pd.read_excel(path, sheet_name="Kn")
    kg = kg.rename(columns={"year": "year"}).astype({"year": int})
    kn = kn.rename(columns={"year": "year"}).astype({"year": int})
    scale_cols = ["Total", "NR", "ME", "NRC", "RC"]
    kg[scale_cols] = kg[scale_cols] * deflator
    kn[scale_cols] = kn[scale_cols] * deflator
    return kg, kn


def to_long(df: pd.DataFrame, value_cols: List[str], var_name: str, value_name: str) -> pd.DataFrame:
    return df.melt(id_vars="year", value_vars=value_cols, var_name=var_name, value_name=value_name)


def compute_overlap_flows(inv: pd.DataFrame, kg_obs: pd.DataFrame, kn_obs: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    assets = ["ME", "NRC", "RC"]
    inv_idx = inv.set_index("year") if "year" in inv.columns else inv
    kg_obs = kg_obs.set_index("year")
    kn_obs = kn_obs.set_index("year")

    flows = []
    for asset in assets:
        kg_series = kg_obs[asset]
        kn_series = kn_obs[asset]
        years = kg_series.index
        delta_kg = kg_series.diff()
        delta_kn = kn_series.diff()
        I_asset = inv_idx.loc[years, f"I_{asset}"]

        r_imp = I_asset - delta_kg
        d_imp = I_asset - delta_kn
        b = kg_series - kn_series
        delta_b = b.diff()
        z = r_imp / kg_series.shift(1)
        delta_rate = d_imp / kn_series.shift(1)

        tmp = pd.DataFrame(
            {
                "year": years,
                "asset": asset,
                "kg_obs": kg_series.values,
                "kn_obs": kn_series.values,
                "r_imp": r_imp.values,
                "d_imp": d_imp.values,
                "b": b.values,
                "delta_b": delta_b.values,
                "z_rate": z.values,
                "delta_rate": delta_rate.values,
            }
        )
        flows.append(tmp)
    return {"overlap": pd.concat(flows, ignore_index=True)}


def weibull_survival(scale: float, shape: float, max_age: int) -> np.ndarray:
    ages = np.arange(max_age + 1)
    surv = np.exp(-((ages / scale) ** shape))
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


def estimate_survival(
    asset: str,
    investment: pd.Series,
    r_imp: pd.Series,
    prior_mean: float,
    log: ViolationLog,
    max_age: int = AGE_MAX,
) -> SurvivalResult:
    valid_all = r_imp.dropna()
    fit_series = valid_all[valid_all >= 0]
    if fit_series.empty:
        scale = prior_mean
        shape = 2.0
        survival = weibull_survival(scale, shape, max_age)
        r_model = retirement_from_survival(investment, survival)
        rmse = float(np.sqrt(((r_model.loc[valid_all.index] - valid_all) ** 2).mean())) if not valid_all.empty else float("nan")
        log.add("survival model misfit", asset, int(investment.index.min()), "No non-negative retirements; falling back to prior", prior_mean)
        return SurvivalResult(
            asset=asset,
            scale=scale,
            shape=shape,
            mean_life=mean_life_weibull(scale, shape),
            rmse=rmse,
            survival=pd.Series(survival, index=np.arange(max_age + 1)),
            retirements_model=r_model,
        )

    years = fit_series.index

    def objective(params: np.ndarray) -> float:
        scale, shape = params
        survival = weibull_survival(scale, shape, max_age)
        r_model = retirement_from_survival(investment, survival)
        diff = (r_model.loc[years] - fit_series) ** 2
        rmse = np.sqrt(diff.mean())
        mean_life = mean_life_weibull(scale, shape)
        penalty = 1.0 * ((mean_life - prior_mean) / prior_mean) ** 2
        return rmse + penalty

    bounds = [(prior_mean * 0.5, prior_mean * 2.5), (0.5, 4.0)]
    x0 = np.array([prior_mean, 2.5])
    result = opt.minimize(objective, x0=x0, bounds=bounds, method="L-BFGS-B")
    scale, shape = result.x
    survival = weibull_survival(scale, shape, max_age)
    r_model = retirement_from_survival(investment, survival)
    rmse = float(np.sqrt(((r_model.loc[valid_all.index] - valid_all) ** 2).mean()))
    mean_life = mean_life_weibull(scale, shape)

    if result.status != 0:
        log.add("survival model misfit", asset, int(years.min()), f"Optimizer status {result.status}", result.fun)

    return SurvivalResult(
        asset=asset,
        scale=float(scale),
        shape=float(shape),
        mean_life=mean_life,
        rmse=rmse,
        survival=pd.Series(survival, index=np.arange(max_age + 1)),
        retirements_model=r_model,
    )


def build_non_overlap_gross(
    investment: pd.DataFrame,
    survival_map: Dict[str, SurvivalResult],
    kg_obs: pd.DataFrame,
) -> Dict[str, pd.Series]:
    kg_obs = kg_obs.set_index("year")
    years = investment.index
    kg_modeled: Dict[str, pd.Series] = {}

    for asset in ASSETS:
        surv = survival_map[asset].survival.values
        kg_model = stock_from_survival(investment[f"I_{asset}"], surv)
        kg_final = kg_model.copy()
        kg_final.loc[(kg_final.index >= OVERLAP_START) & (kg_final.index <= OVERLAP_END)] = kg_obs.loc[
            (kg_obs.index >= OVERLAP_START) & (kg_obs.index <= OVERLAP_END), asset
        ]
        kg_modeled[asset] = kg_final
    kg_modeled["NR"] = kg_modeled["ME"] + kg_modeled["NRC"]
    kg_modeled["Total"] = kg_modeled["ME"] + kg_modeled["NRC"] + kg_modeled["RC"]
    return kg_modeled


def compose_retirements(
    investment: pd.DataFrame,
    survival_map: Dict[str, SurvivalResult],
    r_imp_df: pd.DataFrame,
) -> Dict[str, pd.Series]:
    r_imp = r_imp_df.pivot(index="year", columns="asset", values="r_imp")
    retirements: Dict[str, pd.Series] = {}
    for asset in ASSETS:
        surv = survival_map[asset].survival.values
        r_model = retirement_from_survival(investment[f"I_{asset}"], surv)
        combined = r_model.copy()
        if asset in r_imp.columns:
            combined.update(r_imp[asset])
        retirements[asset] = combined
    retirements["NR"] = retirements["ME"] + retirements["NRC"]
    retirements["Total"] = retirements["ME"] + retirements["NRC"] + retirements["RC"]
    return retirements


def build_gap_ratios(kg_obs: pd.DataFrame, kn_obs: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    kg_obs = kg_obs.set_index("year")
    kn_obs = kn_obs.set_index("year")
    ratios: Dict[str, Dict[str, float]] = {}
    for asset in ASSETS:
        b = kg_obs[asset] - kn_obs[asset]
        gap_ratio = (b / kg_obs[asset]).dropna()
        early = gap_ratio.loc[gap_ratio.index <= OVERLAP_START + 4].median()
        late = gap_ratio.loc[gap_ratio.index >= OVERLAP_END - 4].median()
        ratios[asset] = {"pre": float(early), "post": float(late)}
    return ratios


def build_net_block(
    kg_series: Dict[str, pd.Series],
    kg_obs: pd.DataFrame,
    kn_obs: pd.DataFrame,
    gap_ratios: Dict[str, Dict[str, float]],
) -> Tuple[Dict[str, pd.Series], Dict[str, pd.Series]]:
    kg_obs = kg_obs.set_index("year")
    kn_obs = kn_obs.set_index("year")
    kn_series: Dict[str, pd.Series] = {}
    b_series: Dict[str, pd.Series] = {}
    years = kg_series["ME"].index

    for asset in ASSETS:
        kg = kg_series[asset]
        gap = pd.Series(index=years, dtype=float)
        obs_gap = (kg_obs[asset] - kn_obs[asset])
        gap.loc[obs_gap.index] = obs_gap
        pre_mask = kg.index < OVERLAP_START
        post_mask = kg.index > OVERLAP_END
        gap.loc[pre_mask] = kg.loc[pre_mask] * gap_ratios[asset]["pre"]
        gap.loc[post_mask] = kg.loc[post_mask] * gap_ratios[asset]["post"]
        kn = kg - gap
        kn_series[asset] = kn
        b_series[asset] = gap

    kn_series["NR"] = kn_series["ME"] + kn_series["NRC"]
    kn_series["Total"] = kn_series["ME"] + kn_series["NRC"] + kn_series["RC"]
    b_series["NR"] = b_series["ME"] + b_series["NRC"]
    b_series["Total"] = b_series["ME"] + b_series["NRC"] + b_series["RC"]
    return kn_series, b_series


def compute_depreciation(
    investment: pd.DataFrame,
    kn_series: Dict[str, pd.Series],
) -> Dict[str, pd.Series]:
    depreciation: Dict[str, pd.Series] = {}
    for asset, kn in kn_series.items():
        delta_kn = kn.diff()
        d = investment[f"I_{asset}"] - delta_kn
        depreciation[asset] = d
    return depreciation


def diagnostics_checks(
    kg_series: Dict[str, pd.Series],
    kn_series: Dict[str, pd.Series],
    retirements: Dict[str, pd.Series],
    depreciation: Dict[str, pd.Series],
    b_series: Dict[str, pd.Series],
    log: ViolationLog,
) -> pd.DataFrame:
    records = []
    years = kg_series["ME"].index
    for asset in ["ME", "NRC", "RC", "NR", "Total"]:
        kg = kg_series[asset]
        kn = kn_series[asset]
        r = retirements[asset]
        d = depreciation[asset]
        b = b_series[asset]
        delta_b = b.diff()
        z_rate = r / kg.shift(1)
        delta_rate = d / kn.shift(1)
        for year in years:
            if kg.loc[year] < -1e-6:
                log.add("admissibility", asset, year, "Gross stock negative", kg.loc[year])
            if kn.loc[year] < -1e-6:
                log.add("admissibility", asset, year, "Net stock negative", kn.loc[year])
            if b.loc[year] < -1e-6:
                log.add("admissibility", asset, year, "Capital gap negative", b.loc[year])
            if year > years.min():
                if pd.notna(z_rate.loc[year]) and (z_rate.loc[year] < 0 or z_rate.loc[year] > 1):
                    log.add("rate out of bounds", asset, year, "Retirement rate outside [0,1]", z_rate.loc[year])
                if pd.notna(delta_rate.loc[year]) and (delta_rate.loc[year] < 0 or delta_rate.loc[year] > 1):
                    log.add("rate out of bounds", asset, year, "Depreciation rate outside [0,1]", delta_rate.loc[year])
                bridge_gap = (d.loc[year] - r.loc[year]) - delta_b.loc[year]
                if pd.notna(bridge_gap) and abs(bridge_gap) > ADDITIVITY_TOL * max(abs(b.loc[year]), 1e-9):
                    log.add("definitional mismatch", asset, year, "Bridge identity deviation", bridge_gap)

            records.append(
                {
                    "year": year,
                    "asset": asset,
                    "kg": kg.loc[year],
                    "kn": kn.loc[year],
                    "b": b.loc[year],
                    "r": r.loc[year],
                    "d": d.loc[year],
                    "delta_b": delta_b.loc[year],
                    "z_rate": z_rate.loc[year],
                    "delta_rate": delta_rate.loc[year],
                }
            )
    return pd.DataFrame(records)


def overlap_post_scaling_report(diagnostics: pd.DataFrame, out_path: Path) -> Tuple[str, bool]:
    overlap_df = diagnostics[(diagnostics["year"] >= OVERLAP_START + 1) & (diagnostics["year"] <= OVERLAP_END)].copy()
    assets = ["ME", "NRC", "RC", "NR", "Total"]
    lines: List[str] = []
    stop_flag = False
    overlap_years = len(range(OVERLAP_START + 1, OVERLAP_END + 1))

    for asset in assets:
        sub = overlap_df[overlap_df["asset"] == asset]
        r_neg = (sub["r"] < 0).sum()
        d_neg = (sub["d"] < 0).sum()
        z_out = ((sub["z_rate"] < 0) | (sub["z_rate"] > 1)).sum()
        delta_out = ((sub["delta_rate"] < 0) | (sub["delta_rate"] > 1)).sum()
        z_desc = sub["z_rate"].describe(percentiles=[0.5])[["min", "50%", "max"]]
        delta_desc = sub["delta_rate"].describe(percentiles=[0.5])[["min", "50%", "max"]]
        lines.append(
            f"{asset}: R_imp<0 {r_neg}/{overlap_years} ({r_neg/overlap_years:.3%}); "
            f"D_imp<0 {d_neg}/{overlap_years} ({d_neg/overlap_years:.3%}); "
            f"z out {z_out}/{overlap_years} ({z_out/overlap_years:.3%}); "
            f"delta out {delta_out}/{overlap_years} ({delta_out/overlap_years:.3%}); "
            f"z min/med/max {z_desc['min']:.6f}/{z_desc['50%']:.6f}/{z_desc['max']:.6f}; "
            f"delta min/med/max {delta_desc['min']:.6f}/{delta_desc['50%']:.6f}/{delta_desc['max']:.6f}"
        )
        if asset == "Total" and (r_neg / overlap_years) > 0.01:
            stop_flag = True
    content = "\n".join(lines)
    out_path.write_text(content, encoding="utf-8")
    return content, stop_flag


def save_outputs(
    investment: pd.DataFrame,
    kg_series: Dict[str, pd.Series],
    kn_series: Dict[str, pd.Series],
    retirements: Dict[str, pd.Series],
    depreciation: Dict[str, pd.Series],
    b_series: Dict[str, pd.Series],
    diagnostics: pd.DataFrame,
    survival_results: Dict[str, SurvivalResult],
    deflator: float,
    lambda_bar: float,
    lambda_source: str,
    log: ViolationLog,
    base_dir: Path,
) -> None:
    processed_dir = base_dir / "data" / "processed"
    diag_dir = base_dir / "data" / "diagnostics"
    out_dir = base_dir / "outputs"

    # Harmonized series with stocks
    records = []
    years = investment.index
    assets_all = ["ME", "NRC", "RC", "NR", "Total"]
    for asset in assets_all:
        for year in years:
            records.append({"year": int(year), "asset": asset, "variable": "I", "value": float(investment.loc[year, f"I_{asset}"])})
            records.append({"year": int(year), "asset": asset, "variable": "Kg", "value": float(kg_series[asset].loc[year])})
            records.append({"year": int(year), "asset": asset, "variable": "Kn", "value": float(kn_series[asset].loc[year])})
    harmonized = pd.DataFrame(records)
    harmonized.to_csv(processed_dir / "harmonized_series.csv", index=False)

    # Flows and rates
    flow_records = []
    for asset in assets_all:
        r = retirements[asset]
        d = depreciation[asset]
        b = b_series[asset]
        delta_b = b.diff()
        z_rate = r / kg_series[asset].shift(1)
        delta_rate = d / kn_series[asset].shift(1)
        for year in years:
            flow_records.append(
                {
                    "year": int(year),
                    "asset": asset,
                    "R": float(r.loc[year]) if pd.notna(r.loc[year]) else np.nan,
                    "D": float(d.loc[year]) if pd.notna(d.loc[year]) else np.nan,
                    "B": float(b.loc[year]) if pd.notna(b.loc[year]) else np.nan,
                    "DeltaB": float(delta_b.loc[year]) if pd.notna(delta_b.loc[year]) else np.nan,
                    "z_rate": float(z_rate.loc[year]) if pd.notna(z_rate.loc[year]) else np.nan,
                    "delta_rate": float(delta_rate.loc[year]) if pd.notna(delta_rate.loc[year]) else np.nan,
                }
            )
    flows_df = pd.DataFrame(flow_records)
    flows_df.to_csv(processed_dir / "recovered_flows.csv", index=False)

    diagnostics.to_csv(diag_dir / "flows_and_stocks.csv", index=False)
    log.to_frame().to_csv(out_dir / "violation_log.csv", index=False)
    log.to_frame().to_json(out_dir / "violation_log.json", orient="records", indent=2)

    survival_dump = {
        asset: {
            "family": "weibull",
            "scale": res.scale,
            "shape": res.shape,
            "mean_life": res.mean_life,
            "rmse": res.rmse,
        }
        for asset, res in survival_results.items()
    }
    assumptions = {
        "deflator": "Hofman 1980 -> 2003",
        "deflator_factor": deflator,
        "perez_scaling_applied": True,
        "perez_scaling_lambda_bar": lambda_bar,
        "perez_scaling_source": lambda_source,
        "share_source": "Hofman2000_GrossInvestment.xlsx",
        "control_total": "PerezEyzaguirre_DemandaAgregada.xlsx",
        "share_extension": "ffill/bfill outside Hofman coverage",
        "gap_ratio": "constant pre/post using overlap medians",
        "survival": survival_dump,
    }
    with open(out_dir / "assumptions.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(assumptions, f, sort_keys=False)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    raw_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    diag_dir = base_dir / "data" / "diagnostics"
    out_dir = base_dir / "outputs"
    ensure_dirs([processed_dir, diag_dir, out_dir])

    log = ViolationLog()

    deflator = compute_deflator(raw_dir / "Hofman2000_anchors.xlsx")
    lambda_bar, lambda_source = load_lambda_bar(base_dir)
    control = load_perez(raw_dir / "PerezEyzaguirre_DemandaAgregada.xlsx")
    control["I_tot_control"] = control["I_tot_control"] * lambda_bar
    shares = load_hofman_shares(raw_dir / "Hofman2000_GrossInvestment.xlsx", log)
    shares_ext = extend_shares(shares, control["year"])
    investments = split_investment(control, shares_ext, log)

    kg_obs, kn_obs = load_hofman_stocks(raw_dir / "Hofman_Kstock_gross_net_19501994.xlsx", deflator)
    overlap = compute_overlap_flows(investments, kg_obs, kn_obs)["overlap"]

    survival_results: Dict[str, SurvivalResult] = {}
    for asset in ASSETS:
        r_imp_series = overlap[overlap["asset"] == asset].set_index("year")["r_imp"]
        survival_results[asset] = estimate_survival(
            asset=asset,
            investment=investments.set_index("year")[f"I_{asset}"],
            r_imp=r_imp_series,
            prior_mean=ASSET_PRIORS[asset],
            log=log,
        )

    # Survival fit diagnostics
    fit_records = []
    for asset in ASSETS:
        r_imp_series = overlap[overlap["asset"] == asset].set_index("year")["r_imp"].dropna()
        r_model = survival_results[asset].retirements_model.loc[r_imp_series.index]
        for year in r_imp_series.index:
            fit_records.append(
                {
                    "year": int(year),
                    "asset": asset,
                    "r_imp": float(r_imp_series.loc[year]),
                    "r_model": float(r_model.loc[year]),
                    "residual": float(r_model.loc[year] - r_imp_series.loc[year]),
                }
            )
    pd.DataFrame(fit_records).to_csv(diag_dir / "survival_fit.csv", index=False)

    kg_series = build_non_overlap_gross(investments.set_index("year"), survival_results, kg_obs)
    retirements = compose_retirements(investments.set_index("year"), survival_results, overlap)
    gap_ratios = build_gap_ratios(kg_obs, kn_obs)
    kn_series, b_series = build_net_block(kg_series, kg_obs, kn_obs, gap_ratios)
    depreciation = compute_depreciation(investments.set_index("year"), kn_series)

    diagnostics = diagnostics_checks(kg_series, kn_series, retirements, depreciation, b_series, log)
    post_diag_content, stop_flag = overlap_post_scaling_report(
        diagnostics, diag_dir / "diagnostic_post_scaling.txt"
    )
    print("\nPost-scaling overlap diagnostics:\n" + post_diag_content)

    save_outputs(
        investment=investments.set_index("year"),
        kg_series=kg_series,
        kn_series=kn_series,
        retirements=retirements,
        depreciation=depreciation,
        b_series=b_series,
        diagnostics=diagnostics,
        survival_results=survival_results,
        deflator=deflator,
        lambda_bar=lambda_bar,
        lambda_source=lambda_source,
        log=log,
        base_dir=base_dir,
    )
    if stop_flag:
        print("Scaling did not resolve overlap mismatch; investigate deflator/definition.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
