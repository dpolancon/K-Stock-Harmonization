from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
import yaml

import run_harmonization as base_pipeline


ASSETS = ["ME", "NRC", "RC"]
PANEL_ASSETS = ["ME", "NRC", "RC", "NR", "Total"]
FULL_START = 1900
LEGACY_END = 1994
BCCH_START = 1995
FULL_END = 2024
PK_START = 1940
PK_PRIMARY_START = 1960
OUTPUT_DIRNAME = "HARMONIZED_BCCH_2003CLP_v1"
CANONICAL_COMMAND = "python codes/run_harmonization_bcch.py"
QUALITY_FLAG_MAP = {2023: "provisional", 2024: "preliminary"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_provenance(base_dir: Path, input_paths: List[Path]) -> Dict[str, object]:
    git_commit = base_pipeline.git_stdout(base_dir, ["rev-parse", "HEAD"])
    git_status = base_pipeline.git_stdout(base_dir, ["status", "--porcelain"])
    if git_status is None:
        repo_status = "unknown"
    else:
        repo_status = "clean" if git_status == "" else "dirty"

    input_hashes = {
        base_pipeline.repo_relative(base_dir, path): sha256_file(path)
        for path in input_paths
    }
    return {
        "git_commit": git_commit,
        "python_version": sys.version.split()[0],
        "command": CANONICAL_COMMAND,
        "repo_status": repo_status,
        "input_hashes": input_hashes,
    }


def parse_year_flag(value: object) -> Tuple[int, str]:
    text = str(value).strip()
    match = re.search(r"(\d{4})", text)
    if match is None:
        raise ValueError(f"Could not parse year from BCCh value: {value!r}")
    year = int(match.group(1))
    if "(3)" in text:
        flag = "provisional"
    elif "(4)" in text:
        flag = "preliminary"
    else:
        flag = QUALITY_FLAG_MAP.get(year, "official")
    return year, flag


def find_quality_flags(years: Iterable[int]) -> Dict[int, str]:
    return {int(year): QUALITY_FLAG_MAP[int(year)] for year in years if int(year) in QUALITY_FLAG_MAP}


def load_current_panel(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    return panel[[
        "year",
        "asset",
        "I",
        "Kg",
        "Kn",
        "B",
        "R",
        "D",
        "DeltaKg",
        "DeltaKn",
        "DeltaB",
        "z",
        "delta",
        "residual_kg",
        "residual_kn",
        "I_residual",
    ]].copy()


def load_bcch_real_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    year_flags = [parse_year_flag(value) for value in raw.iloc[9:49, 1].tolist()]
    df = pd.DataFrame(
        {
            "year": [year for year, _ in year_flags],
            "quality_flag": [flag for _, flag in year_flags],
            "RC": raw.iloc[9:49, 2].astype(float).to_numpy() * 1000.0,
            "NRC": raw.iloc[9:49, 3].astype(float).to_numpy() * 1000.0,
            "ME": raw.iloc[9:49, 4].astype(float).to_numpy() * 1000.0,
            "Total_published": raw.iloc[9:49, 5].astype(float).to_numpy() * 1000.0,
        }
    )
    df["NR"] = df["ME"] + df["NRC"]
    df["Total"] = df["NR"] + df["RC"]
    df["raw_total_gap"] = df["Total"] - df["Total_published"]
    return df


def assert_bcch_raw_totals(df: pd.DataFrame, label: str, log: base_pipeline.ViolationLog) -> None:
    for row in df.itertuples(index=False):
        scale = max(abs(row.Total_published), 1.0)
        if abs(row.raw_total_gap) > base_pipeline.ADDITIVITY_TOL * scale:
            log.add(
                "source extraction",
                "Total",
                int(row.year),
                f"BCCh {label} component total does not match published total",
                float(row.raw_total_gap),
            )


def pivot_current(panel: pd.DataFrame, column: str) -> pd.DataFrame:
    return panel.pivot(index="year", columns="asset", values=column)


def build_bridge_factors(current_panel: pd.DataFrame, bcch_kn_raw: pd.DataFrame) -> Dict[str, float]:
    current_1994 = current_panel[current_panel["year"] == LEGACY_END].set_index("asset")
    bcch_1994 = bcch_kn_raw[bcch_kn_raw["year"] == LEGACY_END].iloc[0]
    return {
        asset: float(current_1994.loc[asset, "Kn"] / bcch_1994[asset])
        for asset in ASSETS
    }


def scale_bcch_blocks(
    bcch_kn_raw: pd.DataFrame,
    bcch_d_raw: pd.DataFrame,
    bridge_factors: Dict[str, float],
) -> pd.DataFrame:
    scaled = bcch_kn_raw[["year", "quality_flag"]].copy()
    for asset in ASSETS:
        scaled[f"Kn_{asset}"] = bcch_kn_raw[asset] * bridge_factors[asset]
        scaled[f"D_{asset}"] = bcch_d_raw[asset] * bridge_factors[asset]

    scaled["Kn_NR"] = scaled["Kn_ME"] + scaled["Kn_NRC"]
    scaled["Kn_Total"] = scaled["Kn_NR"] + scaled["Kn_RC"]
    scaled["D_NR"] = scaled["D_ME"] + scaled["D_NRC"]
    scaled["D_Total"] = scaled["D_NR"] + scaled["D_RC"]

    for asset in ASSETS:
        scaled[f"I_{asset}"] = scaled[f"Kn_{asset}"].diff() + scaled[f"D_{asset}"]
    scaled["I_NR"] = scaled["I_ME"] + scaled["I_NRC"]
    scaled["I_Total"] = scaled["I_NR"] + scaled["I_RC"]
    return scaled


def build_full_investment(current_panel: pd.DataFrame, bcch_scaled: pd.DataFrame) -> pd.DataFrame:
    current_i = pivot_current(current_panel, "I")
    full_years = pd.Index(range(FULL_START, FULL_END + 1), name="year")
    investment = pd.DataFrame(index=full_years)

    for asset in ASSETS:
        investment[f"I_{asset}"] = np.nan
        investment.loc[FULL_START:LEGACY_END, f"I_{asset}"] = current_i[asset].to_numpy()
        investment.loc[BCCH_START:FULL_END, f"I_{asset}"] = (
            bcch_scaled.set_index("year").loc[BCCH_START:FULL_END, f"I_{asset}"].to_numpy()
        )

    investment["I_NR"] = investment["I_ME"] + investment["I_NRC"]
    investment["I_Total"] = investment["I_NR"] + investment["I_RC"]
    return investment


def accumulate_gross_and_retirements(
    investment: pd.DataFrame,
    survival_path: Path,
) -> Tuple[Dict[str, pd.Series], Dict[str, pd.Series]]:
    specs = base_pipeline.load_survival_specs(survival_path)
    kg_series: Dict[str, pd.Series] = {}
    retirements: Dict[str, pd.Series] = {}

    for asset in ASSETS:
        survival = base_pipeline.survival_from_spec(specs[asset])
        kg_series[asset] = base_pipeline.stock_from_survival(investment[f"I_{asset}"], survival)
        retirements[asset] = base_pipeline.retirement_from_survival(investment[f"I_{asset}"], survival)

    kg_series["NR"] = kg_series["ME"] + kg_series["NRC"]
    kg_series["Total"] = kg_series["NR"] + kg_series["RC"]
    retirements["NR"] = retirements["ME"] + retirements["NRC"]
    retirements["Total"] = retirements["NR"] + retirements["RC"]
    return kg_series, retirements


def build_scaled_kn_d_series(
    current_panel: pd.DataFrame,
    bcch_scaled: pd.DataFrame,
) -> Tuple[Dict[str, pd.Series], Dict[str, pd.Series]]:
    current_kn = pivot_current(current_panel, "Kn")
    current_d = pivot_current(current_panel, "D")
    bcch_idx = bcch_scaled.set_index("year")
    years = pd.Index(range(FULL_START, FULL_END + 1), name="year")

    kn_series: Dict[str, pd.Series] = {}
    d_series: Dict[str, pd.Series] = {}

    for asset in PANEL_ASSETS:
        kn_series[asset] = pd.Series(index=years, dtype=float)
        d_series[asset] = pd.Series(index=years, dtype=float)
        kn_series[asset].loc[FULL_START:LEGACY_END] = current_kn[asset].to_numpy()
        d_series[asset].loc[FULL_START:LEGACY_END] = current_d[asset].to_numpy()
        kn_series[asset].loc[BCCH_START:FULL_END] = bcch_idx.loc[BCCH_START:FULL_END, f"Kn_{asset}"].to_numpy()
        d_series[asset].loc[BCCH_START:FULL_END] = bcch_idx.loc[BCCH_START:FULL_END, f"D_{asset}"].to_numpy()

    return kn_series, d_series


def build_combined_panel(
    current_panel: pd.DataFrame,
    investment: pd.DataFrame,
    kg_series: Dict[str, pd.Series],
    kn_series: Dict[str, pd.Series],
    retirements: Dict[str, pd.Series],
    d_series: Dict[str, pd.Series],
) -> pd.DataFrame:
    current_sorted = current_panel.copy()
    extension_records: List[Dict[str, float | int | str | None]] = []

    for asset in PANEL_ASSETS:
        current_asset = current_sorted[current_sorted["asset"] == asset].sort_values("year")
        previous = current_asset.iloc[-1].to_dict()

        for year in range(BCCH_START, FULL_END + 1):
            investment_col = f"I_{asset}"
            I = float(investment.loc[year, investment_col])
            Kg = float(kg_series[asset].loc[year])
            Kn = float(kn_series[asset].loc[year])
            B = float(Kg - Kn)
            R = float(retirements[asset].loc[year])
            D = float(d_series[asset].loc[year])
            DeltaKg = Kg - float(previous["Kg"])
            DeltaKn = Kn - float(previous["Kn"])
            DeltaB = B - float(previous["B"])
            z_rate = R / float(previous["Kg"])
            delta_rate = D / float(previous["Kn"])
            residual_kg = DeltaKg - (I - R)
            residual_kn = DeltaKn - (I - D)
            row = {
                "year": year,
                "asset": asset,
                "I": I,
                "Kg": Kg,
                "Kn": Kn,
                "B": B,
                "R": R,
                "D": D,
                "DeltaKg": DeltaKg,
                "DeltaKn": DeltaKn,
                "DeltaB": DeltaB,
                "z": z_rate,
                "delta": delta_rate,
                "residual_kg": residual_kg,
                "residual_kn": residual_kn,
                "I_residual": np.nan,
            }
            extension_records.append(row)
            previous = row

    extension_panel = pd.DataFrame(extension_records)
    total_mask = extension_panel["asset"] == "Total"
    if total_mask.any():
        i_me = extension_panel[extension_panel["asset"] == "ME"]["I"].to_numpy()
        i_nrc = extension_panel[extension_panel["asset"] == "NRC"]["I"].to_numpy()
        i_rc = extension_panel[extension_panel["asset"] == "RC"]["I"].to_numpy()
        extension_panel.loc[total_mask, "I_residual"] = (
            extension_panel.loc[total_mask, "I"].to_numpy() - (i_me + i_nrc + i_rc)
        )

    combined = pd.concat([current_sorted, extension_panel], ignore_index=True)
    combined["asset"] = pd.Categorical(combined["asset"], categories=PANEL_ASSETS, ordered=True)
    combined = combined.sort_values(["asset", "year"]).reset_index(drop=True)
    combined["asset"] = combined["asset"].astype(str)
    return combined


def assert_history_unchanged(current_panel: pd.DataFrame, combined_panel: pd.DataFrame) -> bool:
    legacy = combined_panel[combined_panel["year"] <= LEGACY_END].reset_index(drop=True)
    current = current_panel.reset_index(drop=True)
    return legacy.equals(current)


def load_kn_clio(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Kn_ClioLab")
    return df.rename(
        columns={
            "Kn_ME": "Clio_Kn_ME",
            "Kn_C_CL": "Clio_Kn_C",
            "K_net_tot_CL": "Clio_Kn_Total",
        }
    )


def build_bcch_bridge_diagnostics(
    current_panel: pd.DataFrame,
    bcch_kn_raw: pd.DataFrame,
    bcch_d_raw: pd.DataFrame,
    bcch_scaled: pd.DataFrame,
    kn_clio_path: Path,
    pk_bcch_path: Path,
    bridge_factors: Dict[str, float],
) -> pd.DataFrame:
    current_kn = pivot_current(current_panel, "Kn").add_prefix("current_kn_").reset_index()
    current_d = pivot_current(current_panel, "D").add_prefix("current_d_").reset_index()
    raw_kn = bcch_kn_raw.rename(
        columns={asset: f"raw_kn_{asset}" for asset in ["ME", "NRC", "RC", "NR"]}
    ).rename(
        columns={
            "Total_published": "raw_kn_total_published",
            "Total": "raw_kn_total_components",
            "raw_total_gap": "raw_kn_total_gap",
        }
    )
    raw_d = bcch_d_raw.rename(
        columns={asset: f"raw_d_{asset}" for asset in ["ME", "NRC", "RC", "NR"]}
    ).rename(
        columns={
            "Total_published": "raw_d_total_published",
            "Total": "raw_d_total_components",
            "raw_total_gap": "raw_d_total_gap",
        }
    )

    overlap = raw_kn.merge(
        raw_d[[
            "year",
            *[f"raw_d_{asset}" for asset in ["ME", "NRC", "RC", "NR"]],
            "raw_d_total_published",
            "raw_d_total_components",
            "raw_d_total_gap",
        ]],
        on="year",
        how="left",
    )
    overlap = overlap.merge(current_kn, on="year", how="left")
    overlap = overlap.merge(current_d, on="year", how="left")

    overlap_years = overlap["year"].between(1985, 1994)
    for asset in PANEL_ASSETS:
        overlap[f"overlap_kn_ratio_{asset}"] = np.nan
        overlap[f"overlap_d_ratio_{asset}"] = np.nan
        raw_kn_col = f"raw_kn_{asset}" if asset != "Total" else "raw_kn_total_components"
        raw_d_col = f"raw_d_{asset}" if asset != "Total" else "raw_d_total_components"
        overlap.loc[overlap_years, f"overlap_kn_ratio_{asset}"] = (
            overlap.loc[overlap_years, f"current_kn_{asset}"] / overlap.loc[overlap_years, raw_kn_col]
        )
        overlap.loc[overlap_years, f"overlap_d_ratio_{asset}"] = (
            overlap.loc[overlap_years, f"current_d_{asset}"] / overlap.loc[overlap_years, raw_d_col]
        )

    diagnostics = overlap[[
        "year",
        "quality_flag",
        "raw_kn_total_published",
        "raw_kn_total_components",
        "raw_kn_total_gap",
        "raw_d_total_published",
        "raw_d_total_components",
        "raw_d_total_gap",
        *[f"overlap_kn_ratio_{asset}" for asset in PANEL_ASSETS],
        *[f"overlap_d_ratio_{asset}" for asset in PANEL_ASSETS],
    ]].copy()

    diagnostics["bridge_factor_ME"] = bridge_factors["ME"]
    diagnostics["bridge_factor_NRC"] = bridge_factors["NRC"]
    diagnostics["bridge_factor_RC"] = bridge_factors["RC"]

    scaled_cols = [
        "year",
        "Kn_ME",
        "Kn_NRC",
        "Kn_RC",
        "Kn_NR",
        "Kn_Total",
        "D_ME",
        "D_NRC",
        "D_RC",
        "D_NR",
        "D_Total",
        "I_ME",
        "I_NRC",
        "I_RC",
        "I_NR",
        "I_Total",
    ]
    diagnostics = diagnostics.merge(bcch_scaled[scaled_cols], on="year", how="left")

    clio = load_kn_clio(kn_clio_path)
    diagnostics = diagnostics.merge(clio, on="year", how="left")
    diagnostics["scaled_vs_clio_ratio_ME"] = diagnostics["Kn_ME"] / diagnostics["Clio_Kn_ME"]
    diagnostics["scaled_vs_clio_ratio_C"] = (diagnostics["Kn_RC"] + diagnostics["Kn_NRC"]) / diagnostics["Clio_Kn_C"]
    diagnostics["scaled_vs_clio_ratio_Total"] = diagnostics["Kn_Total"] / diagnostics["Clio_Kn_Total"]

    bcch_pk = pd.read_excel(pk_bcch_path, sheet_name="BCCh_referencia2018").rename(columns=lambda col: str(col).strip())
    bcch_pk["year"] = pd.to_datetime(bcch_pk["year"]).dt.year.astype(int)
    diagnostics = diagnostics.merge(
        bcch_pk[["year", "FBKF_real"]].rename(columns={"FBKF_real": "BCCh_FBKF_real"}),
        on="year",
        how="left",
    )
    diagnostics["scaled_I_total_to_BCCh_FBKF_real_ratio"] = diagnostics["I_Total"] / (diagnostics["BCCh_FBKF_real"] * 1000.0)
    return diagnostics


def build_bcch_bridge_summary(
    diagnostics: pd.DataFrame,
    bridge_factors: Dict[str, float],
    history_unchanged: bool,
) -> str:
    overlap = diagnostics[(diagnostics["year"] >= 1985) & (diagnostics["year"] <= 1994)]
    lines = [
        "BCCh bridge audit 1985-1994",
        f"Legacy history through 1994 preserved exactly: {history_unchanged}",
        f"Max raw Kn total add-up gap: {diagnostics['raw_kn_total_gap'].abs().max():.6f}",
        f"Max raw D total add-up gap: {diagnostics['raw_d_total_gap'].abs().max():.6f}",
        "1994 hard-anchor bridge factors:",
        *(f"- {asset}: {bridge_factors[asset]:.12f}" for asset in ["ME", "NRC", "RC"]),
        "Median overlap ratios (current / raw BCCh):",
    ]
    for asset in PANEL_ASSETS:
        kn_ratio = overlap[f"overlap_kn_ratio_{asset}"].median()
        d_ratio = overlap[f"overlap_d_ratio_{asset}"].median()
        lines.append(f"- {asset}: Kn={kn_ratio:.6f}; D={d_ratio:.6f}")
    lines.extend(
        [
            "Secondary diagnostics:",
            f"- Median scaled BCCh / Clio ratio (ME, 1985-2010): {diagnostics.loc[diagnostics['year'].between(1985, 2010), 'scaled_vs_clio_ratio_ME'].median():.6f}",
            f"- Median scaled BCCh / Clio ratio (Construction, 1985-2010): {diagnostics.loc[diagnostics['year'].between(1985, 2010), 'scaled_vs_clio_ratio_C'].median():.6f}",
            f"- Median scaled BCCh / Clio ratio (Total, 1985-2010): {diagnostics.loc[diagnostics['year'].between(1985, 2010), 'scaled_vs_clio_ratio_Total'].median():.6f}",
            f"- Median implied-I / BCCh real FBKF ratio (1986-2024): {diagnostics.loc[diagnostics['year'].between(1986, 2024), 'scaled_I_total_to_BCCh_FBKF_real_ratio'].median():.6f}",
        ]
    )
    return "\n".join(lines)


def load_bcch_pk(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="BCCh_referencia2018").rename(columns=lambda col: str(col).strip())
    df["year"] = pd.to_datetime(df["year"]).dt.year.astype(int)
    df["Pk_ratio_raw"] = df["FBKF_nom"] / df["FBKF_real"]
    df["Pk_published_2003base"] = df["Pk"] / float(df.loc[df["year"] == 2003, "Pk"].iloc[0]) * 100.0
    df["Pk_ratio_2003base"] = df["Pk_ratio_raw"] / float(df.loc[df["year"] == 2003, "Pk_ratio_raw"].iloc[0]) * 100.0
    df["Pk_2003base"] = df["Pk_ratio_2003base"]
    df["source"] = "BCCh_ratio_nom_over_real"
    df["quality_flag"] = df["year"].map(QUALITY_FLAG_MAP).fillna("official")
    return df


def load_clio_pk(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="ig_nom_ig_real_Pk")
    df["year"] = df["year"].astype(int)
    df["Pk_published_2003base"] = df["Pk"] / float(df.loc[df["year"] == 2003, "Pk"].iloc[0]) * 100.0
    df["Pk_ratio_2003base"] = (
        (df["FBKFNOM"] / df["FBKFREAL"]) / float((df["FBKFNOM"] / df["FBKFREAL"]).loc[df["year"] == 2003].iloc[0]) * 100.0
    )
    df["Pk_2003base"] = df["Pk_ratio_2003base"]
    return df


def build_pk_panel(
    bcch_pk_path: Path,
    clio_pk_path: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    bcch = load_bcch_pk(bcch_pk_path)
    clio = load_clio_pk(clio_pk_path)

    clio_1960 = float(clio.loc[clio["year"] == PK_PRIMARY_START, "Pk_ratio_2003base"].iloc[0])
    pk_1960 = float(bcch.loc[bcch["year"] == PK_PRIMARY_START, "Pk_2003base"].iloc[0])
    chained = {PK_PRIMARY_START: pk_1960}
    clio_idx = clio.set_index("year")
    for year in range(PK_PRIMARY_START - 1, PK_START - 1, -1):
        next_year = year + 1
        growth = float(clio_idx.loc[next_year, "Pk_ratio_2003base"] / clio_idx.loc[year, "Pk_ratio_2003base"])
        chained[year] = chained[next_year] / growth

    pre_bcch = pd.DataFrame(
        {
            "year": list(range(PK_START, PK_PRIMARY_START)),
            "Pk_2003base": [chained[year] for year in range(PK_START, PK_PRIMARY_START)],
            "source": "Clio_ratio_growth_chained_to_BCCh_ratio_1960",
            "quality_flag": "historical",
        }
    )

    pk_panel = pd.concat(
        [
            pre_bcch,
            bcch.loc[bcch["year"] >= PK_PRIMARY_START, ["year", "Pk_2003base", "source", "quality_flag"]],
        ],
        ignore_index=True,
    ).sort_values("year").reset_index(drop=True)

    diagnostics = pk_panel.merge(
        bcch[["year", "Pk_2003base", "Pk_ratio_raw", "Pk_ratio_2003base"]].rename(
            columns={
                "Pk_2003base": "BCCh_Pk_production_2003base",
                "Pk_ratio_raw": "BCCh_Pk_ratio_raw",
                "Pk_ratio_2003base": "BCCh_Pk_ratio_2003base",
            }
        ),
        on="year",
        how="left",
    ).merge(
        clio[["year", "Pk_2003base", "Pk_ratio_2003base"]].rename(
            columns={
                "Pk_2003base": "Clio_Pk_production_2003base",
                "Pk_ratio_2003base": "Clio_Pk_ratio_2003base",
            }
        ),
        on="year",
        how="left",
    )
    diagnostics["source_switch"] = diagnostics["year"] == PK_PRIMARY_START

    stats = {
        "pk_1960_anchor_level": pk_1960,
        "clio_1960_2003base": clio_1960,
    }
    return pk_panel, diagnostics, stats


def assert_pk_panel(pk_panel: pd.DataFrame) -> None:
    expected_years = list(range(PK_START, FULL_END + 1))
    if pk_panel["year"].tolist() != expected_years:
        raise ValueError("Pk panel does not cover a continuous 1940-2024 span.")
    pk_2003 = float(pk_panel.loc[pk_panel["year"] == 2003, "Pk_2003base"].iloc[0])
    if abs(pk_2003 - 100.0) > 1e-9:
        raise ValueError(f"Pk(2003) expected 100.0, found {pk_2003}")


def build_full_summary(panel: pd.DataFrame, log: base_pipeline.ViolationLog) -> Tuple[str, bool]:
    violations = log.to_frame()
    source_issues = violations[violations["type"] == "source extraction"]
    admissibility = violations[violations["type"] == "admissibility"]
    mismatch = violations[violations["type"] == "definitional mismatch"]
    rate_out = violations[violations["type"] == "rate out of bounds"]
    post_bcch_rate_out = rate_out[rate_out["year"] >= BCCH_START]

    meets_bar = source_issues.empty and admissibility.empty and mismatch.empty and rate_out.empty
    lines = [
        "Full-period audit 1900-2024",
        f"Source extraction issues: {len(source_issues)}",
        f"Negative stock/gap violations: {len(admissibility)}",
        f"Identity/additivity violations: {len(mismatch)}",
        f"Rate out-of-bounds violations (all years): {len(rate_out)}",
        f"Rate out-of-bounds violations (1995-2024): {len(post_bcch_rate_out)}",
        f"Status: {'PASS' if meets_bar else 'FAIL'}",
    ]
    return "\n".join(lines), meets_bar


def format_csv_value(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, (np.floating, float)):
        return format(float(value), ".17g")
    return str(value)


def write_panel_csv_with_legacy_preservation(
    panel: pd.DataFrame,
    legacy_panel_path: Path,
    out_path: Path,
) -> None:
    with legacy_panel_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        legacy_rows_by_asset: Dict[str, List[Dict[str, str]]] = {asset: [] for asset in PANEL_ASSETS}
        for row in reader:
            legacy_rows_by_asset[row["asset"]].append(row)

    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for asset in PANEL_ASSETS:
            for row in legacy_rows_by_asset[asset]:
                writer.writerow(row)
            extension_rows = panel[(panel["asset"] == asset) & (panel["year"] > LEGACY_END)]
            for row in extension_rows.itertuples(index=False):
                writer.writerow(
                    {
                        "year": str(row.year),
                        "asset": row.asset,
                        "I": format_csv_value(row.I),
                        "Kg": format_csv_value(row.Kg),
                        "Kn": format_csv_value(row.Kn),
                        "B": format_csv_value(row.B),
                        "R": format_csv_value(row.R),
                        "D": format_csv_value(row.D),
                        "DeltaKg": format_csv_value(row.DeltaKg),
                        "DeltaKn": format_csv_value(row.DeltaKn),
                        "DeltaB": format_csv_value(row.DeltaB),
                        "z": format_csv_value(row.z),
                        "delta": format_csv_value(row.delta),
                        "residual_kg": format_csv_value(row.residual_kg),
                        "residual_kn": format_csv_value(row.residual_kn),
                        "I_residual": format_csv_value(row.I_residual),
                    }
                )


def write_outputs(
    base_dir: Path,
    panel: pd.DataFrame,
    pk_panel: pd.DataFrame,
    bridge_diagnostics: pd.DataFrame,
    pk_diagnostics: pd.DataFrame,
    bridge_summary: str,
    full_summary: str,
    log: base_pipeline.ViolationLog,
    metadata: Dict[str, object],
) -> None:
    out_dir = base_dir / "outputs" / OUTPUT_DIRNAME
    base_pipeline.ensure_dirs([out_dir])

    write_panel_csv_with_legacy_preservation(
        panel=panel,
        legacy_panel_path=Path(metadata["legacy_panel_source"]),
        out_path=out_dir / "harmonized_series_2003CLP_1900_2024.csv",
    )
    panel.to_excel(
        out_dir / "harmonized_series_2003CLP_1900_2024.xlsx",
        index=False,
        sheet_name="harmonized_panel",
        float_format="%.17g",
    )
    base_pipeline.normalize_xlsx(out_dir / "harmonized_series_2003CLP_1900_2024.xlsx")

    master_panel = panel.merge(pk_panel[["year", "Pk_2003base"]], on="year", how="left")
    master_panel.to_csv(
        out_dir / "harmonized_master_dataset_2003CLP_1900_2024.csv",
        index=False,
        float_format="%.17g",
    )
    master_panel.to_excel(
        out_dir / "harmonized_master_dataset_2003CLP_1900_2024.xlsx",
        index=False,
        sheet_name="master_harmonized_dataset",
        float_format="%.17g",
    )
    base_pipeline.normalize_xlsx(out_dir / "harmonized_master_dataset_2003CLP_1900_2024.xlsx")

    pk_panel.to_csv(out_dir / "harmonized_pk_2003base_1940_2024.csv", index=False, float_format="%.17g")
    pk_panel.to_excel(
        out_dir / "harmonized_pk_2003base_1940_2024.xlsx",
        index=False,
        sheet_name="harmonized_pk",
        float_format="%.17g",
    )
    base_pipeline.normalize_xlsx(out_dir / "harmonized_pk_2003base_1940_2024.xlsx")

    bridge_diagnostics.to_csv(out_dir / "bcch_bridge_diagnostics.csv", index=False, float_format="%.17g")
    pk_diagnostics.to_csv(out_dir / "pk_splice_diagnostics.csv", index=False, float_format="%.17g")
    log.to_frame().to_csv(out_dir / "violation_log.csv", index=False)
    (out_dir / "bcch_bridge_audit_summary_1985_1994.txt").write_text(bridge_summary + "\n", encoding="utf-8")
    (out_dir / "audit_summary_full_1900_2024.txt").write_text(full_summary + "\n", encoding="utf-8")

    assumptions = {
        "primary_price_space": "2003 CLP",
        "bundle_type": "additive BCCh extension",
        "command": metadata["command"],
        "git_commit": metadata["git_commit"],
        "generated_by": OUTPUT_DIRNAME,
        "python_version": metadata["python_version"],
        "repo_status": metadata["repo_status"],
        "history_through_1994_exact": metadata["history_through_1994_exact"],
        "bcch_start_year": BCCH_START,
        "pk_start_year": PK_START,
        "pk_primary_start_year": PK_PRIMARY_START,
        "bridge_rule": "1994 hard anchor by asset on Kn; same asset factor applied to D",
        "bridge_factors_1994": metadata["bridge_factors_1994"],
        "pk_splice_rule": "BCCh ratio deflator (FBKF_nom/FBKF_real) rebased to 2003=100 for 1960-2024; ClioLab ratio deflator growth chained backward to the BCCh ratio level at 1960 for 1940-1959",
        "source_quality_flags": metadata["source_quality_flags"],
        "bcch_recent_year_flags": metadata["bcch_recent_year_flags"],
        "pk_recent_year_flags": dict(metadata["bcch_recent_year_flags"]),
        "survival_parameter_source": metadata["survival_parameter_source"],
        "legacy_panel_source": metadata["legacy_panel_source"],
        "bcch_stock_source": metadata["bcch_stock_source"],
        "bcch_pk_source": metadata["bcch_pk_source"],
        "clio_pk_source": metadata["clio_pk_source"],
        "kn_clio_diagnostic_source": metadata["kn_clio_diagnostic_source"],
        "pk_2003base_anchor_check": metadata["pk_2003base_anchor_check"],
        "meets_full_period_admissibility": metadata["meets_full_period_admissibility"],
        "input_hashes": metadata["input_hashes"],
    }
    assumptions = base_pipeline.stabilize_provenance(out_dir / "assumptions.yaml", assumptions)
    with (out_dir / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(assumptions, handle, sort_keys=False)

    summary_lines = [
        f"# {OUTPUT_DIRNAME} summary",
        "",
        "Additive BCCh extension bundle in constant 2003 CLP.",
        "The legacy Perez-based 1900-1994 production surface remains frozen and is preserved exactly inside this bundle.",
        "",
        "## Status",
        f"- Legacy 1900-1994 history preserved exactly: {metadata['history_through_1994_exact']}",
        f"- BCCh forward-extension start year: {BCCH_START}",
        f"- Full-period admissibility: {metadata['meets_full_period_admissibility']}",
        f"- Pk coverage: {PK_START}-{FULL_END}",
        f"- Pk(2003)=100 check: {metadata['pk_2003base_anchor_check']}",
        "",
        "## Provenance",
        f"- Generated at UTC: {assumptions['generated_at_utc']}",
        f"- Git commit: {assumptions['git_commit']}",
        f"- Repo status at generation: {assumptions['repo_status']}",
        f"- Command: {assumptions['command']}",
        "",
        "## Bridge factors (1994)",
        *(f"- {asset}: {value:.12f}" for asset, value in metadata["bridge_factors_1994"].items()),
        "",
        "## Pk splice",
        "- Primary source 1960-2024: ratio deflator `FBKF_nom / FBKF_real` from `data/raw/BCCH_ref2018_Pk.xlsx`, rebased to 2003=100.",
        "- Backcast source 1940-1959: ClioLab ratio-deflator growth chained to the BCCh ratio level at 1960.",
        "",
        "## Notes",
        "- BCCh published totals for stocks and depreciation are used only as extraction audits; production aggregates are recomputed from components.",
        "- `Kn_ClioLab.xlsx` and BCCh total real FBKF remain diagnostic-only inputs.",
        "- Years 2023 and 2024 are flagged as provisional and preliminary, respectively, in the diagnostic and Pk outputs.",
    ]
    (out_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    raw_dir = base_dir / "data" / "raw"
    output_dir = base_dir / "outputs"

    legacy_panel_path = output_dir / "HARMONIZED_PEREZ_2003CLP_v1" / "harmonized_series_2003CLP_1900_1994.csv"
    survival_path = output_dir / "survival_fit_hofman_1980.csv"
    bcch_stock_path = raw_dir / "BCCH_1985_2024.xlsx"
    bcch_pk_path = raw_dir / "BCCH_ref2018_Pk.xlsx"
    clio_pk_path = raw_dir / "ClioLab_GFKF_Freal_nominal_Pk.xlsx"
    kn_clio_path = raw_dir / "Kn_ClioLab.xlsx"

    required_inputs = [
        legacy_panel_path,
        survival_path,
        bcch_stock_path,
        bcch_pk_path,
        clio_pk_path,
        kn_clio_path,
    ]

    log = base_pipeline.ViolationLog()
    current_panel = load_current_panel(legacy_panel_path)
    bcch_kn_raw = load_bcch_real_sheet(bcch_stock_path, "1")
    bcch_d_raw = load_bcch_real_sheet(bcch_stock_path, "2")
    assert_bcch_raw_totals(bcch_kn_raw, "Kn", log)
    assert_bcch_raw_totals(bcch_d_raw, "D", log)

    bridge_factors = build_bridge_factors(current_panel, bcch_kn_raw)
    bcch_scaled = scale_bcch_blocks(bcch_kn_raw, bcch_d_raw, bridge_factors)
    investment = build_full_investment(current_panel, bcch_scaled)
    kg_series, retirements = accumulate_gross_and_retirements(investment, survival_path)
    kn_series, d_series = build_scaled_kn_d_series(current_panel, bcch_scaled)
    panel = build_combined_panel(current_panel, investment, kg_series, kn_series, retirements, d_series)
    history_unchanged = assert_history_unchanged(current_panel, panel)
    if not history_unchanged:
        raise ValueError("Legacy 1900-1994 history drifted in the BCCh extension bundle.")

    base_pipeline.diagnostics_checks(panel, log)
    full_summary, full_ok = build_full_summary(panel, log)

    bridge_diagnostics = build_bcch_bridge_diagnostics(
        current_panel=current_panel,
        bcch_kn_raw=bcch_kn_raw,
        bcch_d_raw=bcch_d_raw,
        bcch_scaled=bcch_scaled,
        kn_clio_path=kn_clio_path,
        pk_bcch_path=bcch_pk_path,
        bridge_factors=bridge_factors,
    )
    bridge_summary = build_bcch_bridge_summary(bridge_diagnostics, bridge_factors, history_unchanged)

    pk_panel, pk_diagnostics, pk_stats = build_pk_panel(bcch_pk_path, clio_pk_path)
    assert_pk_panel(pk_panel)

    metadata = build_provenance(base_dir, required_inputs)
    metadata.update(
        {
            "history_through_1994_exact": history_unchanged,
            "bridge_factors_1994": bridge_factors,
            "source_quality_flags": {
                "historical": "Clio backcast for Pk only, 1940-1959",
                "official": "BCCh source series used to compute ratio-deflator production values",
                "provisional": "BCCh 2023 provisional",
                "preliminary": "BCCh 2024 preliminary",
            },
            "bcch_recent_year_flags": find_quality_flags([2023, 2024]),
            "survival_parameter_source": str(survival_path),
            "legacy_panel_source": str(legacy_panel_path),
            "bcch_stock_source": str(bcch_stock_path),
            "bcch_pk_source": str(bcch_pk_path),
            "clio_pk_source": str(clio_pk_path),
            "kn_clio_diagnostic_source": str(kn_clio_path),
            "pk_2003base_anchor_check": True,
            "meets_full_period_admissibility": full_ok,
        }
    )

    write_outputs(
        base_dir=base_dir,
        panel=panel,
        pk_panel=pk_panel,
        bridge_diagnostics=bridge_diagnostics,
        pk_diagnostics=pk_diagnostics,
        bridge_summary=bridge_summary,
        full_summary=full_summary,
        log=log,
        metadata=metadata,
    )

    print(bridge_summary)
    print("")
    print(full_summary)
    if not full_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
