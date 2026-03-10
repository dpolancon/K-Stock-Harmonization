from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Dict, Iterable, List, Tuple
import zipfile

import numpy as np
import pandas as pd
import yaml


ASSETS = ["ME", "NRC", "RC"]
PANEL_ASSETS = ["ME", "NRC", "RC", "NR", "Total"]
OVERLAP_START = 1950
OVERLAP_END = 1994
ADDITIVITY_TOL = 0.005
IDENTITY_ABS_TOL = 1e-6
AGE_MAX = 150
EARLY_RATE_OUT_MAX = 0
REGRESSION_INVEST_TOL = 1e-6
REGRESSION_STOCK_TOL = 1e-6
CANONICAL_COMMAND = "python codes/run_harmonization.py"

DEFERRED_SOURCES = [
    "BCCH_1985_2024.xlsx",
    "BCCH_ref2018_Pk.xlsx",
    "ClioLab_GFKF_Freal_nominal_Pk.xlsx",
    "Kn_ClioLab.xlsx",
    "Tafunell_Ducoing_2016_Kg.xlsx",
    "tafunel_2013_Ig.xlsx",
]


@dataclass
class SurvivalSpec:
    asset: str
    scale: float
    shape: float
    mean_life: float
    rmse: float
    family: str
    status: str


class ViolationLog:
    def __init__(self) -> None:
        self.records: List[Dict[str, object]] = []

    def add(self, vtype: str, asset: str, year: int, message: str, value: float | None) -> None:
        self.records.append(
            {
                "type": vtype,
                "asset": asset,
                "year": int(year),
                "message": message,
                "value": None if value is None or pd.isna(value) else float(value),
            }
        )

    def to_frame(self) -> pd.DataFrame:
        if not self.records:
            return pd.DataFrame(columns=["type", "asset", "year", "message", "value"])
        return pd.DataFrame(self.records)


def ensure_dirs(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def repo_relative(base_dir: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_stdout(base_dir: Path, args: List[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=base_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def build_provenance(base_dir: Path, input_paths: List[Path]) -> Dict[str, object]:
    git_commit = git_stdout(base_dir, ["rev-parse", "HEAD"])
    git_status = git_stdout(base_dir, ["status", "--porcelain"])
    if git_status is None:
        repo_status = "unknown"
    else:
        repo_status = "clean" if git_status == "" else "dirty"

    input_hashes = {repo_relative(base_dir, path): sha256_file(path) for path in input_paths}
    return {
        "git_commit": git_commit,
        "python_version": sys.version.split()[0],
        "command": CANONICAL_COMMAND,
        "repo_status": repo_status,
        "input_hashes": input_hashes,
    }


def stabilize_provenance(assumptions_path: Path, assumptions: Dict[str, object]) -> Dict[str, object]:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if not assumptions_path.exists():
        assumptions["generated_at_utc"] = generated_at
        return assumptions

    try:
        existing = yaml.safe_load(assumptions_path.read_text(encoding="utf-8")) or {}
    except Exception:
        assumptions["generated_at_utc"] = generated_at
        return assumptions

    current_compare = dict(assumptions)
    existing_compare = dict(existing)
    for field in ["generated_at_utc", "git_commit"]:
        current_compare.pop(field, None)
        existing_compare.pop(field, None)

    if current_compare == existing_compare:
        if existing.get("git_commit"):
            assumptions["git_commit"] = existing["git_commit"]
        if existing.get("generated_at_utc"):
            assumptions["generated_at_utc"] = existing["generated_at_utc"]
            return assumptions

    assumptions["generated_at_utc"] = generated_at
    return assumptions


def normalize_xlsx(path: Path) -> None:
    fixed_dt = (1980, 1, 1, 0, 0, 0)
    fixed_w3cdtf = "1980-01-01T00:00:00Z"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", dir=path.parent) as temp_handle:
        temp_path = Path(temp_handle.name)

    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for name in sorted(source.namelist()):
                payload = source.read(name)
                if name == "docProps/core.xml":
                    payload = re.sub(
                        rb"<dcterms:(created|modified)[^>]*>.*?</dcterms:\1>",
                        lambda match: match.group(0).split(b">", 1)[0] + b">" + fixed_w3cdtf.encode("utf-8") + b"</dcterms:" + match.group(1) + b">",
                        payload,
                    )
                info = zipfile.ZipInfo(filename=name, date_time=fixed_dt)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 0
                target.writestr(info, payload)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def find_column_any(columns: List[str], needles: List[str]) -> str:
    normalized = {str(column): str(column).casefold() for column in columns}
    for needle in needles:
        needle_cf = needle.casefold()
        for column, column_cf in normalized.items():
            if needle_cf in column_cf:
                return column
    raise ValueError(f"Column containing any of {needles} not found.")


def load_perez_ex_inventory(path: Path) -> Tuple[pd.DataFrame, Dict[str, object]]:
    raw_header = pd.read_excel(path, sheet_name="Demanda Agregada", header=None)
    header_note = " | ".join(str(value) for value in raw_header.iloc[0].tolist() if isinstance(value, str))

    df = pd.read_excel(path, sheet_name="Demanda Agregada", header=0)
    df = df.rename(columns={df.columns[0]: "year"})
    df["year"] = df["year"].astype(int)

    maquinaria_col = find_column_any(list(df.columns), ["FBKF en maquinaria"])
    construccion_col = find_column_any(list(df.columns), ["FBKF en construccion", "FBKF en construcción"])
    inventarios_col = find_column_any(list(df.columns), ["Variacion de inventarios", "Variación de inventarios"])

    out = df[["year", maquinaria_col, construccion_col, inventarios_col]].copy()
    out = out.rename(
        columns={
            maquinaria_col: "perez_fbfk_maquinaria",
            construccion_col: "perez_fbfk_construccion",
            inventarios_col: "perez_inventarios",
        }
    )
    out["I_control_ex_inventory"] = out["perez_fbfk_maquinaria"] + out["perez_fbfk_construccion"]
    out = out[(out["year"] >= 1900) & (out["year"] <= 1994)].copy()

    metadata = {
        "source_file": str(path),
        "sheet": "Demanda Agregada",
        "header_note": header_note,
        "columns_used": {
            "FBKF en maquinaria": maquinaria_col,
            "FBKF en construccion": construccion_col,
            "Variacion de inventarios": inventarios_col,
        },
        "control_concept": "FBKF ex inventories",
        "inventories_excluded_from_accumulation": True,
    }
    return out, metadata


def load_hofman_investment(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Gross_Investment_Ig_Hofman2000")
    df = df.rename(
        columns={
            "year": "year",
            "Ig_ME_H2000": "I_ME",
            "Ig_NRC_H2000": "I_NRC",
            "Ig_RC_H2000": "I_RC",
            "Ig_tot_H2000": "I_tot",
        }
    )
    df["year"] = df["year"].astype(int)
    return df[["year", "I_ME", "I_NRC", "I_RC", "I_tot"]].copy()


def load_hofman_shares(path: Path, years: pd.Index, log: ViolationLog) -> pd.DataFrame:
    df = load_hofman_investment(path)

    for component in ASSETS:
        df[f"share_{component}_raw"] = df[f"I_{component}"] / df["I_tot"]
    df["share_sum_raw"] = df[["share_ME_raw", "share_NRC_raw", "share_RC_raw"]].sum(axis=1)

    bad_sum = df["share_sum_raw"].dropna()
    for idx, value in bad_sum[(bad_sum - 1.0).abs() > ADDITIVITY_TOL].items():
        log.add(
            "share normalization",
            "Total",
            int(df.loc[idx, "year"]),
            "Hofman raw asset shares do not sum to 1; normalizing shares for production harmonization",
            value - 1.0,
        )

    for component in ASSETS:
        df[f"share_{component}"] = df[f"share_{component}_raw"] / df["share_sum_raw"]

    shares = df[["year", "share_ME", "share_NRC", "share_RC"]].set_index("year")
    shares = shares.reindex(years).ffill().bfill()
    shares["share_NR"] = shares["share_ME"] + shares["share_NRC"]
    return shares.reset_index()


def load_lambda_choice(path: Path) -> Tuple[float, Dict[str, object]]:
    if not path.exists():
        raise FileNotFoundError(f"Lambda estimates file not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if "lambda_choice" not in payload:
        raise ValueError(f"lambda_choice missing in {path}")
    lambda_choice = float(payload["lambda_choice"])
    stats = {
        "lambda_choice": lambda_choice,
        "lambda_median": float(payload.get("lambda_median", lambda_choice)),
        "lambda_mean": float(payload.get("lambda_mean", lambda_choice)),
        "lambda_trim10": float(payload.get("lambda_trim10", lambda_choice)),
        "n_obs": int(payload.get("n_obs", 0)),
        "lambda_rule": payload.get("lambda_rule", "unknown"),
    }
    return lambda_choice, stats


def weibull_survival(scale: float, shape: float, max_age: int) -> np.ndarray:
    ages = np.arange(max_age + 1)
    survival = np.exp(-((ages / scale) ** shape))
    survival[0] = 1.0
    return survival


def rectangular_survival(life: float, max_age: int) -> np.ndarray:
    ages = np.arange(max_age + 1)
    survival = (ages <= life).astype(float)
    survival[0] = 1.0
    return survival


def retirement_from_survival(investment: pd.Series, survival: np.ndarray) -> pd.Series:
    kernel = np.concatenate([[0.0], survival[:-1] - survival[1:]])
    values = np.convolve(investment.values, kernel, mode="full")[: len(investment)]
    return pd.Series(values, index=investment.index)


def stock_from_survival(investment: pd.Series, survival: np.ndarray) -> pd.Series:
    values = np.convolve(investment.values, survival, mode="full")[: len(investment)]
    return pd.Series(values, index=investment.index)


def load_survival_specs(path: Path) -> Dict[str, SurvivalSpec]:
    if not path.exists():
        raise FileNotFoundError(f"Survival parameter file not found: {path}")
    df = pd.read_csv(path)
    specs: Dict[str, SurvivalSpec] = {}
    for asset in ASSETS:
        row = df[df["asset"] == asset]
        if row.empty:
            raise ValueError(f"Survival parameters missing for asset: {asset}")
        record = row.iloc[0]
        specs[asset] = SurvivalSpec(
            asset=asset,
            scale=float(record["scale"]),
            shape=float(record["shape"]),
            mean_life=float(record.get("mean_life", np.nan)),
            rmse=float(record.get("rmse", np.nan)),
            family=str(record.get("family", "weibull")),
            status=str(record.get("status", "unknown")),
        )
    return specs


def survival_from_spec(spec: SurvivalSpec) -> np.ndarray:
    if spec.family.lower() == "rectangular":
        life = spec.mean_life if np.isfinite(spec.mean_life) else spec.scale
        return rectangular_survival(life, AGE_MAX)
    if not np.isfinite(spec.shape):
        life = spec.mean_life if np.isfinite(spec.mean_life) else spec.scale
        return rectangular_survival(life, AGE_MAX)
    return weibull_survival(spec.scale, spec.shape, AGE_MAX)


def build_gap_ratios_from_baseline(path: Path) -> Dict[str, Dict[str, float]]:
    if not path.exists():
        raise FileNotFoundError(f"Frozen baseline panel not found: {path}")
    panel = pd.read_csv(path)
    kg_idx = panel.pivot(index="year", columns="asset", values="Kg")
    kn_idx = panel.pivot(index="year", columns="asset", values="Kn")
    ratios: Dict[str, Dict[str, float]] = {}
    for asset in ASSETS:
        gap_ratio = ((kg_idx[asset] - kn_idx[asset]) / kg_idx[asset]).replace([np.inf, -np.inf], np.nan).dropna()
        early = gap_ratio.loc[gap_ratio.index <= OVERLAP_START + 4].median()
        late = gap_ratio.loc[gap_ratio.index >= OVERLAP_END - 4].median()
        overall = gap_ratio.median()
        if pd.isna(early):
            early = overall
        if pd.isna(late):
            late = overall
        ratios[asset] = {"pre": float(early), "post": float(late)}
    return ratios


def build_investment_block(
    raw_dir: Path,
    lambda_path: Path,
    log: ViolationLog,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    target_years = pd.Index(range(1900, 1995), name="year")

    perez, perez_meta = load_perez_ex_inventory(raw_dir / "PerezEyzaguirre_DemandaAgregada.xlsx")
    perez = perez.set_index("year").reindex(target_years)
    if perez["I_control_ex_inventory"].isna().any():
        missing_years = perez[perez["I_control_ex_inventory"].isna()].index.tolist()
        raise ValueError(f"Perez control total missing for years: {missing_years}")

    lambda_choice, lambda_stats = load_lambda_choice(lambda_path)
    shares = load_hofman_shares(raw_dir / "Hofman2000_GrossInvestment.xlsx", target_years, log).set_index("year")

    investment = perez.join(shares, how="left")
    investment["I_control_scaled"] = investment["I_control_ex_inventory"] * lambda_choice
    investment["I_ME"] = investment["I_control_scaled"] * investment["share_ME"]
    investment["I_NRC"] = investment["I_control_scaled"] * investment["share_NRC"]
    investment["I_RC"] = investment["I_control_scaled"] * investment["share_RC"]
    investment["I_NR"] = investment["I_ME"] + investment["I_NRC"]
    investment["I_Total"] = investment["I_ME"] + investment["I_NRC"] + investment["I_RC"]

    rel_gap = (investment["I_Total"] - investment["I_control_scaled"]) / investment["I_control_scaled"]
    for year, value in rel_gap[rel_gap.abs() > ADDITIVITY_TOL].items():
        log.add("definitional mismatch", "Total", int(year), "Split investment does not add to scaled control total", value)

    metadata = {
        "lambda_choice": float(lambda_choice),
        "lambda_rule": lambda_stats.get("lambda_rule", "unknown"),
        "lambda_stats": lambda_stats,
        "lambda_source": str(lambda_path),
        "control_total_definition": "Perez FBKF en maquinaria + FBKF en construccion",
        "inventories_excluded_from_accumulation": True,
        "perez_metadata": perez_meta,
        "hofman_share_source": str(raw_dir / "Hofman2000_GrossInvestment.xlsx"),
    }
    return investment, metadata


def accumulate_stocks(
    investment: pd.DataFrame,
    survival_specs: Dict[str, SurvivalSpec],
) -> Tuple[Dict[str, pd.Series], Dict[str, pd.Series]]:
    kg_series: Dict[str, pd.Series] = {}
    retirements: Dict[str, pd.Series] = {}

    for asset in ASSETS:
        spec = survival_specs[asset]
        survival = survival_from_spec(spec)
        kg_series[asset] = stock_from_survival(investment[f"I_{asset}"], survival)
        retirements[asset] = retirement_from_survival(investment[f"I_{asset}"], survival)

    kg_series["NR"] = kg_series["ME"] + kg_series["NRC"]
    kg_series["Total"] = kg_series["ME"] + kg_series["NRC"] + kg_series["RC"]
    retirements["NR"] = retirements["ME"] + retirements["NRC"]
    retirements["Total"] = retirements["ME"] + retirements["NRC"] + retirements["RC"]
    return kg_series, retirements


def build_net_block(
    kg_series: Dict[str, pd.Series],
    gap_ratios: Dict[str, Dict[str, float]],
) -> Tuple[Dict[str, pd.Series], Dict[str, pd.Series]]:
    years = kg_series["ME"].index
    kn_series: Dict[str, pd.Series] = {}
    b_series: Dict[str, pd.Series] = {}

    for asset in ASSETS:
        kg = kg_series[asset]
        gap = pd.Series(index=years, dtype=float)
        pre_mask = gap.index < OVERLAP_START
        gap.loc[pre_mask] = kg.loc[pre_mask] * gap_ratios[asset]["pre"]
        gap.loc[~pre_mask] = kg.loc[~pre_mask] * gap_ratios[asset]["post"]
        kn_series[asset] = kg - gap
        b_series[asset] = gap

    kn_series["NR"] = kn_series["ME"] + kn_series["NRC"]
    b_series["NR"] = b_series["ME"] + b_series["NRC"]
    kn_series["Total"] = kn_series["ME"] + kn_series["NRC"] + kn_series["RC"]
    b_series["Total"] = b_series["ME"] + b_series["NRC"] + b_series["RC"]
    return kn_series, b_series


def compute_depreciation(investment: pd.DataFrame, kn_series: Dict[str, pd.Series]) -> Dict[str, pd.Series]:
    depreciation: Dict[str, pd.Series] = {}
    for asset in PANEL_ASSETS:
        depreciation[asset] = investment[f"I_{asset}"] - kn_series[asset].diff()
    return depreciation


def compose_panel(
    investment: pd.DataFrame,
    kg_series: Dict[str, pd.Series],
    kn_series: Dict[str, pd.Series],
    retirements: Dict[str, pd.Series],
    depreciation: Dict[str, pd.Series],
    b_series: Dict[str, pd.Series],
) -> pd.DataFrame:
    records: List[Dict[str, float | int | str | None]] = []
    years = investment.index

    for asset in PANEL_ASSETS:
        kg = kg_series[asset]
        kn = kn_series[asset]
        b = b_series[asset]
        r = retirements[asset]
        d = depreciation[asset]
        i = investment[f"I_{asset}"]
        delta_kg = kg.diff()
        delta_kn = kn.diff()
        delta_b = b.diff()
        z_rate = r / kg.shift(1)
        delta_rate = d / kn.shift(1)
        residual_kg = delta_kg - (i - r)
        residual_kn = delta_kn - (i - d)

        for year in years:
            records.append(
                {
                    "year": int(year),
                    "asset": asset,
                    "I": float(i.loc[year]),
                    "Kg": float(kg.loc[year]),
                    "Kn": float(kn.loc[year]),
                    "B": float(b.loc[year]),
                    "R": float(r.loc[year]) if pd.notna(r.loc[year]) else np.nan,
                    "D": float(d.loc[year]) if pd.notna(d.loc[year]) else np.nan,
                    "DeltaKg": float(delta_kg.loc[year]) if pd.notna(delta_kg.loc[year]) else np.nan,
                    "DeltaKn": float(delta_kn.loc[year]) if pd.notna(delta_kn.loc[year]) else np.nan,
                    "DeltaB": float(delta_b.loc[year]) if pd.notna(delta_b.loc[year]) else np.nan,
                    "z": float(z_rate.loc[year]) if pd.notna(z_rate.loc[year]) else np.nan,
                    "delta": float(delta_rate.loc[year]) if pd.notna(delta_rate.loc[year]) else np.nan,
                    "residual_kg": float(residual_kg.loc[year]) if pd.notna(residual_kg.loc[year]) else np.nan,
                    "residual_kn": float(residual_kn.loc[year]) if pd.notna(residual_kn.loc[year]) else np.nan,
                }
            )

    panel = pd.DataFrame(records)
    total_i = investment["I_ME"] + investment["I_NRC"] + investment["I_RC"]
    panel["I_residual"] = np.nan
    total_mask = panel["asset"] == "Total"
    panel.loc[total_mask, "I_residual"] = panel.loc[total_mask, "I"].values - total_i.values
    return panel


def add_additivity_checks(panel: pd.DataFrame, log: ViolationLog) -> None:
    for year in sorted(panel["year"].unique()):
        subset = panel[panel["year"] == year].set_index("asset")
        nr_kg_gap = subset.loc["NR", "Kg"] - (subset.loc["ME", "Kg"] + subset.loc["NRC", "Kg"])
        nr_kn_gap = subset.loc["NR", "Kn"] - (subset.loc["ME", "Kn"] + subset.loc["NRC", "Kn"])
        nr_i_gap = subset.loc["NR", "I"] - (subset.loc["ME", "I"] + subset.loc["NRC", "I"])
        total_kg_gap = subset.loc["Total", "Kg"] - (subset.loc["ME", "Kg"] + subset.loc["NRC", "Kg"] + subset.loc["RC", "Kg"])
        total_kn_gap = subset.loc["Total", "Kn"] - (subset.loc["ME", "Kn"] + subset.loc["NRC", "Kn"] + subset.loc["RC", "Kn"])
        total_i_gap = subset.loc["Total", "I"] - (subset.loc["ME", "I"] + subset.loc["NRC", "I"] + subset.loc["RC", "I"])

        checks = [
            ("NR", "NR Kg additivity", nr_kg_gap, subset.loc["NR", "Kg"]),
            ("NR", "NR Kn additivity", nr_kn_gap, subset.loc["NR", "Kn"]),
            ("NR", "NR I additivity", nr_i_gap, subset.loc["NR", "I"]),
            ("Total", "Total Kg additivity", total_kg_gap, subset.loc["Total", "Kg"]),
            ("Total", "Total Kn additivity", total_kn_gap, subset.loc["Total", "Kn"]),
            ("Total", "Total I additivity", total_i_gap, subset.loc["Total", "I"]),
        ]
        for asset, message, gap, scale in checks:
            if abs(gap) > ADDITIVITY_TOL * max(abs(scale), 1.0):
                log.add("definitional mismatch", asset, int(year), message, gap)


def diagnostics_checks(panel: pd.DataFrame, log: ViolationLog) -> None:
    add_additivity_checks(panel, log)
    min_year = int(panel["year"].min())

    for row in panel.itertuples(index=False):
        if row.Kg < -IDENTITY_ABS_TOL:
            log.add("admissibility", row.asset, int(row.year), "Gross stock negative", row.Kg)
        if row.Kn < -IDENTITY_ABS_TOL:
            log.add("admissibility", row.asset, int(row.year), "Net stock negative", row.Kn)
        if row.B < -IDENTITY_ABS_TOL:
            log.add("admissibility", row.asset, int(row.year), "Capital gap negative", row.B)
        if int(row.year) > min_year:
            if pd.notna(row.z) and (row.z < 0 or row.z > 1):
                log.add("rate out of bounds", row.asset, int(row.year), "Retirement rate outside [0,1]", row.z)
            if pd.notna(row.delta) and (row.delta < 0 or row.delta > 1):
                log.add("rate out of bounds", row.asset, int(row.year), "Depreciation rate outside [0,1]", row.delta)
            if pd.notna(row.residual_kg) and abs(row.residual_kg) > IDENTITY_ABS_TOL:
                log.add("definitional mismatch", row.asset, int(row.year), "DeltaKg identity residual", row.residual_kg)
            if pd.notna(row.residual_kn) and abs(row.residual_kn) > IDENTITY_ABS_TOL:
                log.add("definitional mismatch", row.asset, int(row.year), "DeltaKn identity residual", row.residual_kn)
            bridge_gap = (row.D - row.R) - row.DeltaB if pd.notna(row.DeltaB) else np.nan
            if pd.notna(bridge_gap) and abs(bridge_gap) > IDENTITY_ABS_TOL:
                log.add("definitional mismatch", row.asset, int(row.year), "Bridge identity deviation", bridge_gap)


def build_overlap_summary(panel: pd.DataFrame) -> Tuple[str, bool]:
    overlap = panel[(panel["year"] >= OVERLAP_START) & (panel["year"] <= OVERLAP_END)].copy()
    overlap_years = overlap["year"].nunique()
    lines = ["Overlap audit 1950-1994"]
    meets_bar = True

    for asset in PANEL_ASSETS:
        subset = overlap[overlap["asset"] == asset]
        r_neg = int((subset["R"] < 0).sum())
        d_neg = int((subset["D"] < 0).sum())
        z_bad = int(((subset["z"] < 0) | (subset["z"] > 1)).sum())
        delta_bad = int(((subset["delta"] < 0) | (subset["delta"] > 1)).sum())
        lines.append(
            f"{asset}: R<0 {r_neg}/{overlap_years}; D<0 {d_neg}/{overlap_years}; z out {z_bad}/{overlap_years}; delta out {delta_bad}/{overlap_years}"
        )
        if any([r_neg, d_neg, z_bad, delta_bad]):
            meets_bar = False

    lines.append(f"Status: {'PASS' if meets_bar else 'FAIL'}")
    return "\n".join(lines), meets_bar


def build_full_summary(panel: pd.DataFrame, log: ViolationLog) -> Tuple[str, bool, int]:
    violations = log.to_frame()
    admissibility = violations[violations["type"] == "admissibility"]
    mismatch = violations[violations["type"] == "definitional mismatch"]
    rate_out = violations[violations["type"] == "rate out of bounds"]
    early_rate_out = rate_out[rate_out["year"] < OVERLAP_START]
    overlap_or_late_rate_out = rate_out[rate_out["year"] >= OVERLAP_START]

    meets_bar = (
        admissibility.empty
        and mismatch.empty
        and overlap_or_late_rate_out.empty
        and len(early_rate_out) <= EARLY_RATE_OUT_MAX
    )
    lines = [
        "Full-period audit 1900-1994",
        f"Negative stock/gap violations: {len(admissibility)}",
        f"Identity/additivity violations: {len(mismatch)}",
        f"Rate out-of-bounds violations (all years): {len(rate_out)}",
        f"Rate out-of-bounds violations (<1950): {len(early_rate_out)}",
        f"Rate out-of-bounds violations (>=1950): {len(overlap_or_late_rate_out)}",
        f"Early-rate tolerance (max allowed): {EARLY_RATE_OUT_MAX}",
        f"Status: {'PASS' if meets_bar else 'FAIL'}",
    ]
    return "\n".join(lines), meets_bar, len(early_rate_out)


def compare_with_reference(panel: pd.DataFrame, base_dir: Path) -> Tuple[Dict[str, float], bool]:
    metrics: Dict[str, float] = {}
    ok = True

    investment_ref = (
        base_dir
        / "outputs"
        / "EXTENSION_INVESTMENT_BLOCK_CANDIDATE_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1"
        / "investment_block_candidate_1900_1994.csv"
    )
    if investment_ref.exists():
        ref = pd.read_csv(investment_ref)
        merged = panel[["year", "asset", "I"]].merge(
            ref[["year", "asset", "I_candidate"]],
            on=["year", "asset"],
            how="inner",
        )
        merged["abs_diff"] = (merged["I"] - merged["I_candidate"]).abs()
        for asset in PANEL_ASSETS:
            subset = merged[merged["asset"] == asset]
            if not subset.empty:
                max_diff = float(subset["abs_diff"].max())
                metrics[f"investment_max_abs_diff_{asset}"] = max_diff
                if max_diff > REGRESSION_INVEST_TOL:
                    ok = False

    stock_ref = (
        base_dir
        / "outputs"
        / "EXTENSION_CANDIDATE_STOCKS_PEREZ_SCALED_HOFMAN_SHARES_2003CLP_v1"
        / "candidate_stocks_1900_1994.csv"
    )
    if stock_ref.exists():
        ref = pd.read_csv(stock_ref)
        for asset in ["ME", "NRC", "RC", "Total"]:
            kg_col = f"Kg_{asset}"
            kn_col = f"Kn_{asset}"
            if kg_col in ref.columns:
                subset = panel[panel["asset"] == asset][["year", "Kg", "Kn"]].merge(
                    ref[["year", kg_col, kn_col]],
                    on="year",
                    how="inner",
                )
                kg_diff = float((subset["Kg"] - subset[kg_col]).abs().max())
                kn_diff = float((subset["Kn"] - subset[kn_col]).abs().max())
                metrics[f"kg_max_abs_diff_{asset}"] = kg_diff
                metrics[f"kn_max_abs_diff_{asset}"] = kn_diff
                if kg_diff > REGRESSION_STOCK_TOL or kn_diff > REGRESSION_STOCK_TOL:
                    ok = False

    return metrics, ok


def write_outputs(
    panel: pd.DataFrame,
    log: ViolationLog,
    base_dir: Path,
    metadata: Dict[str, object],
    regression_metrics: Dict[str, float],
    regression_ok: bool,
    overlap_ok: bool,
    full_ok: bool,
    early_rate_out_count: int,
) -> None:
    out_dir = base_dir / "outputs" / "HARMONIZED_PEREZ_2003CLP_v1"
    ensure_dirs([out_dir])

    panel.to_csv(out_dir / "harmonized_series_2003CLP_1900_1994.csv", index=False)
    panel.to_excel(
        out_dir / "harmonized_series_2003CLP_1900_1994.xlsx",
        index=False,
        sheet_name="harmonized_panel",
    )
    normalize_xlsx(out_dir / "harmonized_series_2003CLP_1900_1994.xlsx")
    log.to_frame().to_csv(out_dir / "violation_log.csv", index=False)

    overlap_text, _ = build_overlap_summary(panel)
    full_text, _, _ = build_full_summary(panel, log)
    (out_dir / "overlap_audit_summary.txt").write_text(overlap_text + "\n", encoding="utf-8")
    (out_dir / "audit_summary_full_1900_1994.txt").write_text(full_text + "\n", encoding="utf-8")

    assumptions = {
        "primary_price_space": "2003 CLP",
        "control_concept": "FBKF ex inventories",
        "inventories_excluded_from_accumulation": True,
        "git_commit": metadata["git_commit"],
        "python_version": metadata["python_version"],
        "command": metadata["command"],
        "repo_status": metadata["repo_status"],
        "lambda_choice": metadata["lambda_choice"],
        "lambda_rule": metadata["lambda_rule"],
        "lambda_stats": metadata["lambda_stats"],
        "lambda_source": metadata["lambda_source"],
        "hofman_share_source": metadata["hofman_share_source"],
        "survival_parameter_source": metadata["survival_parameter_source"],
        "gap_ratio_source": metadata["gap_ratio_source"],
        "frozen_baseline_reference": metadata["frozen_baseline_reference"],
        "deferred_sources": DEFERRED_SOURCES,
        "perez_metadata": metadata["perez_metadata"],
        "regression_vs_extension_candidate": regression_metrics,
        "regression_ok": regression_ok,
        "meets_overlap_admissibility": overlap_ok,
        "meets_full_period_admissibility": full_ok,
        "early_rate_out_count": early_rate_out_count,
        "early_rate_out_max": EARLY_RATE_OUT_MAX,
        "input_hashes": metadata["input_hashes"],
    }
    assumptions = stabilize_provenance(out_dir / "assumptions.yaml", assumptions)
    with (out_dir / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(assumptions, handle, sort_keys=False)

    summary_lines = [
        "# HARMONIZED_PEREZ_2003CLP_v1 summary",
        "",
        "Canonical harmonized baseline built from Perez FBKF ex inventories scaled by lambda_choice and split by normalized Hofman shares.",
        "Frozen Hofman 1980 baseline remains unchanged.",
        "",
        "## Status",
        f"- Primary price space: {assumptions['primary_price_space']}",
        f"- Control concept: {assumptions['control_concept']}",
        f"- Inventories excluded from accumulation: {assumptions['inventories_excluded_from_accumulation']}",
        f"- Meets overlap admissibility bar: {overlap_ok}",
        f"- Meets full-period admissibility bar: {full_ok}",
        f"- Regression vs extension candidate: {regression_ok}",
        f"- Early rate out-of-bounds count (<1950): {early_rate_out_count}",
        f"- Early rate tolerance (max allowed): {EARLY_RATE_OUT_MAX}",
        "",
        "## Provenance",
        f"- Generated at UTC: {assumptions['generated_at_utc']}",
        f"- Git commit: {assumptions['git_commit']}",
        f"- Repo status at generation: {assumptions['repo_status']}",
        f"- Command: {assumptions['command']}",
        "",
        "## Regression vs extension candidate",
    ]
    if regression_metrics:
        for key, value in sorted(regression_metrics.items()):
            summary_lines.append(f"- {key}: {value:.12f}")
    else:
        summary_lines.append("- Reference extension outputs not found; regression comparison skipped.")

    summary_lines.extend(
        [
            "",
            "## Deferred non-Perez sources",
            *(f"- {source}" for source in DEFERRED_SOURCES),
            "",
            "## Notes",
            "- Inventories remain outside fixed-capital accumulation because the repo models fixed capital only (ME, NRC, RC).",
            "- The canonical production command is `codes/run_harmonization.py`.",
            "- The canonical production artifacts are written to `outputs/HARMONIZED_PEREZ_2003CLP_v1/`.",
            "- Exact required-input hashes are recorded in `assumptions.yaml`.",
        ]
    )
    (out_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    raw_dir = base_dir / "data" / "raw"

    lambda_path = base_dir / "outputs" / "DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1" / "lambda_estimates.yaml"
    survival_path = base_dir / "outputs" / "survival_fit_hofman_1980.csv"
    gap_ratio_path = base_dir / "outputs" / "harmonized_series_1980CLP_1900_1994.csv"
    required_inputs = [
        raw_dir / "PerezEyzaguirre_DemandaAgregada.xlsx",
        raw_dir / "Hofman2000_GrossInvestment.xlsx",
        lambda_path,
        survival_path,
        gap_ratio_path,
    ]

    log = ViolationLog()

    investment, metadata = build_investment_block(raw_dir, lambda_path, log)
    survival_specs = load_survival_specs(survival_path)
    gap_ratios = build_gap_ratios_from_baseline(gap_ratio_path)

    kg_series, retirements = accumulate_stocks(investment, survival_specs)
    kn_series, b_series = build_net_block(kg_series, gap_ratios)
    depreciation = compute_depreciation(investment, kn_series)
    panel = compose_panel(investment, kg_series, kn_series, retirements, depreciation, b_series)
    diagnostics_checks(panel, log)

    metadata.update(
        {
            "survival_parameter_source": str(survival_path),
            "gap_ratio_source": str(gap_ratio_path),
            "frozen_baseline_reference": str(gap_ratio_path),
            **build_provenance(base_dir, required_inputs),
        }
    )

    regression_metrics, regression_ok = compare_with_reference(panel, base_dir)
    overlap_text, overlap_ok = build_overlap_summary(panel)
    full_text, full_ok, early_rate_out_count = build_full_summary(panel, log)

    write_outputs(panel, log, base_dir, metadata, regression_metrics, regression_ok, overlap_ok, full_ok, early_rate_out_count)

    print(overlap_text)
    print("")
    print(full_text)
    if not overlap_ok or not full_ok or not regression_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
