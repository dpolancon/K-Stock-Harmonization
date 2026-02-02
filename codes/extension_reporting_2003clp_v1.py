from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
BASELINE_SERIES = BASE_DIR / "outputs" / "harmonized_series_1980CLP_1900_1994.csv"
BASELINE_ASSUMPTIONS = BASE_DIR / "outputs" / "assumptions.yaml"
OUTPUT_DIR = BASE_DIR / "outputs" / "EXTENSION_REPORTING_2003CLP_v1"

VALUE_COLUMNS = ["I", "Kg", "Kn", "B", "R", "D", "DeltaKg", "DeltaKn"]
ASSET_GROUPS = ["ME", "NRC", "RC", "NR", "C", "T", "Total"]


def load_deflator(path: Path) -> float:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if "deflator_factor" not in payload:
        raise KeyError("deflator_factor missing from assumptions.yaml")
    return float(payload["deflator_factor"])


def scale_series(df: pd.DataFrame, factor: float) -> pd.DataFrame:
    out = df.copy()
    present_cols = [col for col in VALUE_COLUMNS if col in out.columns]
    out[present_cols] = out[present_cols] * factor
    return out


def compute_identity_residuals(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for asset in ASSET_GROUPS:
        subset = df[df["asset"] == asset].sort_values("year")
        if subset.empty:
            continue
        delta_kg = subset["Kg"].diff()
        delta_kn = subset["Kn"].diff()
        residual_kg = delta_kg - (subset["I"] - subset["R"])
        residual_kn = delta_kn - (subset["I"] - subset["D"])
        temp = pd.DataFrame(
            {
                "year": subset["year"].values,
                "asset": asset,
                "residual_delta_kg": residual_kg.values,
                "residual_delta_kn": residual_kn.values,
            }
        )
        records.append(temp)
    residuals = pd.concat(records, ignore_index=True)

    def add_additivity(check_asset: str, left_assets: list[str]) -> pd.DataFrame:
        left = df[df["asset"].isin(left_assets)].pivot(index="year", columns="asset", values="Kg")
        right = df[df["asset"] == check_asset].set_index("year")
        kg_resid = right["Kg"] - left.sum(axis=1)
        kn_resid = right["Kn"] - df[df["asset"].isin(left_assets)].pivot(index="year", columns="asset", values="Kn").sum(axis=1)
        i_resid = right["I"] - df[df["asset"].isin(left_assets)].pivot(index="year", columns="asset", values="I").sum(axis=1)
        return pd.DataFrame(
            {
                "year": kg_resid.index,
                "asset": check_asset,
                "additivity_kg": kg_resid.values,
                "additivity_kn": kn_resid.values,
                "additivity_i": i_resid.values,
            }
        )

    additivity = pd.concat(
        [
            add_additivity("NR", ["ME", "NRC"]),
            add_additivity("T", ["ME", "C"]),
        ],
        ignore_index=True,
    )
    residuals = residuals.merge(additivity, on=["year", "asset"], how="left")
    return residuals


def write_assumptions(deflator: float) -> None:
    payload = {
        "extension": "EXTENSION_REPORTING_2003CLP_v1",
        "classification": "Reporting-space extension",
        "baseline_series": str(BASELINE_SERIES),
        "deflator_source": "outputs/assumptions.yaml (computed from data/raw/Hofman2000_anchors.xlsx)",
        "deflator_factor": deflator,
        "from_price_year": 1980,
        "to_price_year": 2003,
        "notes": "Baseline values preserved; scaled outputs only for reporting.",
    }
    with (OUTPUT_DIR / "assumptions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def write_summary(residuals: pd.DataFrame) -> None:
    summary_path = OUTPUT_DIR / "summary.md"
    max_abs = residuals[["residual_delta_kg", "residual_delta_kn", "additivity_kg", "additivity_kn", "additivity_i"]].abs().max()
    lines = [
        "# EXTENSION_REPORTING_2003CLP_v1 summary",
        "",
        "Converted baseline harmonized series from constant 1980 CLP to constant 2003 CLP using a single deflator.",
        "Baseline outputs are unchanged; only reporting-space outputs were created.",
        "",
        "## Identity checks (max absolute residual)",
        f"- ΔKg = Ig − R: {max_abs['residual_delta_kg']:.6f}",
        f"- ΔKn = Ig − D: {max_abs['residual_delta_kn']:.6f}",
        f"- NR = ME + NRC (Kg/Kn/I): {max_abs['additivity_kg']:.6f} / {max_abs['additivity_kn']:.6f} / {max_abs['additivity_i']:.6f}",
        f"- T = ME + C (Kg/Kn/I): {max_abs['additivity_kg']:.6f} / {max_abs['additivity_kn']:.6f} / {max_abs['additivity_i']:.6f}",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    deflator = load_deflator(BASELINE_ASSUMPTIONS)
    baseline = pd.read_csv(BASELINE_SERIES)
    baseline = baseline[baseline["asset"].isin(ASSET_GROUPS)].copy()
    converted = scale_series(baseline, deflator)

    converted.to_csv(OUTPUT_DIR / "converted_series_2003CLP_1900_1994.csv", index=False)

    residuals = compute_identity_residuals(converted)
    residuals.to_csv(OUTPUT_DIR / "identity_residuals_2003CLP.csv", index=False)

    write_assumptions(deflator)
    write_summary(residuals)


if __name__ == "__main__":
    main()
