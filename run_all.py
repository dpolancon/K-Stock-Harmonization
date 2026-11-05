#!/usr/bin/env python3
"""
Master Reproduction Entry-Point
K-Stock-Harmonization: Harmonized Net and Gross Capital Stocks for Chile (1900-2024)

This script executes the complete sequence of computational steps required to reproduce
all publication-grade accounting and harmonized surfaces from raw data inputs.

Usage:
    python run_all.py
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time


STEPS = [
    {
        "name": "Step 1: Frozen Accounting Reference (Hofman 1980 CLP)",
        "script": "codes/run_baseline_hofman_1980.py",
        "output_check": "outputs/harmonized_series_1980CLP_1900_1994.csv",
    },
    {
        "name": "Step 2: Canonical Harmonized Baseline (Perez 2003 CLP, 1900-1994)",
        "script": "codes/run_harmonization.py",
        "output_check": "outputs/HARMONIZED_PEREZ_2003CLP_v1/harmonized_series_2003CLP_1900_1994.csv",
    },
    {
        "name": "Step 3: Additive BCCh Extension Bundle & Master Dataset (2003 CLP, 1900-2024)",
        "script": "codes/run_harmonization_bcch.py",
        "output_check": "outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_master_dataset_2003CLP_1900_2024.csv",
    },
]


def run_step(step: dict, base_dir: Path) -> bool:
    print(f"\n{'=' * 70}")
    print(f"Executing {step['name']}")
    print(f"Command: python {step['script']}")
    print(f"{'=' * 70}\n")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(base_dir / step["script"])],
            cwd=base_dir,
            check=True,
            text=True,
        )
        elapsed = time.time() - start_time
        print(f"\n[PASS] {step['name']} completed in {elapsed:.2f}s")
        
        out_file = base_dir / step["output_check"]
        if not out_file.exists():
            print(f"[ERROR] Expected output artifact missing: {out_file}")
            return False
        return True
    except subprocess.CalledProcessError as err:
        print(f"\n[FAIL] {step['name']} exited with code {err.returncode}")
        return False
    except Exception as exc:
        print(f"\n[ERROR] Unexpected error executing {step['script']}: {exc}")
        return False


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    print("=" * 70)
    print("K-Stock-Harmonization: Full Master Reproduction Pipeline")
    print(f"Working Directory: {base_dir}")
    print(f"Python Executable: {sys.executable}")
    print("=" * 70)

    success_count = 0
    total_start = time.time()

    for step in STEPS:
        if run_step(step, base_dir):
            success_count += 1
        else:
            print(f"\n[ABORT] Pipeline stopped due to failure in step: {step['name']}")
            sys.exit(1)

    total_elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print(f"REPRODUCTION PIPELINE COMPLETE: {success_count}/{len(STEPS)} steps passed.")
    print(f"Total Execution Time: {total_elapsed:.2f} seconds")
    print("Definitive Master Dataset:")
    print(f"  -> {base_dir / 'outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_master_dataset_2003CLP_1900_2024.csv'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
