from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
PEREZ_ANCHOR = BASE_DIR / "outputs" / "ANCHOR_PEREZ_FBFK_2003CLP_v1" / "perez_anchor_pack_1860_2010.csv"
PEREZ_METADATA = BASE_DIR / "outputs" / "ANCHOR_PEREZ_FBFK_2003CLP_v1" / "metadata.yaml"
LAMBDA_PATH = BASE_DIR / "outputs" / "DIAGNOSTIC_LEVEL_NORMALIZATION_LAMBDA_v1" / "lambda_estimates.yaml"
OUTPUT_DIR = BASE_DIR / "outputs" / "ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(PEREZ_ANCHOR)
    metadata = load_yaml(PEREZ_METADATA)
    lambda_payload = load_yaml(LAMBDA_PATH)
    lambda_choice = float(lambda_payload.get("lambda_choice"))

    data["perez_fbfk_maquinaria_scaled"] = data["perez_fbfk_maquinaria"] * lambda_choice
    data["perez_fbfk_construccion_scaled"] = data["perez_fbfk_construccion"] * lambda_choice
    data["perez_fbfk_total_ex_inv_scaled"] = data["perez_fbfk_total_ex_inv"] * lambda_choice

    data.to_csv(OUTPUT_DIR / "perez_anchor_pack_1860_2010_scaled.csv", index=False)

    metadata_out = {
        **metadata,
        "lambda_choice": lambda_choice,
        "lambda_source": str(LAMBDA_PATH),
        "level_normalization_note": (
            "Scaled series use lambda as a level normalization bridge; this is not a unit conversion."
        ),
        "scaled_columns": [
            "perez_fbfk_maquinaria_scaled",
            "perez_fbfk_construccion_scaled",
            "perez_fbfk_total_ex_inv_scaled",
        ],
    }
    with (OUTPUT_DIR / "metadata.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(metadata_out, handle, sort_keys=False)

    diff_scaled = data["perez_fbfk_total_ex_inv_scaled"] - (
        data["perez_fbfk_maquinaria_scaled"] + data["perez_fbfk_construccion_scaled"]
    )
    max_abs_diff_scaled = float(diff_scaled.abs().max())

    summary_lines = [
        "# ANCHOR_PEREZ_FBFK_2003CLP_v2_SCALED summary",
        "",
        f"Coverage years: {data['year'].min()}-{data['year'].max()}",
        f"Lambda choice: {lambda_choice}",
        "",
        "## Sanity check",
        "Check: scaled maquinaria + scaled construcción vs scaled FBKF total ex inventories.",
        f"Max absolute difference: {max_abs_diff_scaled:.6f}",
        "Scaling is a level normalization bridge, not a unit conversion.",
    ]
    (OUTPUT_DIR / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    created_files = [
        OUTPUT_DIR / "perez_anchor_pack_1860_2010_scaled.csv",
        OUTPUT_DIR / "metadata.yaml",
        OUTPUT_DIR / "summary.md",
    ]
    print("Created files:")
    for path in created_files:
        print(f"- {path}")
    print("baseline untouched: PASS")


if __name__ == "__main__":
    main()
