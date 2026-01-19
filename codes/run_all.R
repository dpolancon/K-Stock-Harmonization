############################################################
## 99_run_all.R — TD–SFC MASTER PIPELINE RUNNER
## Runs the entire workflow in correct dependency order.
## Stops on error. Prints progress banners.
############################################################

library(here)

run_safe <- function(script_path) {
  message("\n--------------------------------------------------")
  message("Running: ", script_path)
  message("--------------------------------------------------\n")
  tryCatch(
    {
      source(script_path, echo = TRUE, max.deparse.length = Inf)
      message("\n✓ Completed: ", script_path, "\n")
    },
    error = function(e) {
      message("\n✗ ERROR in ", script_path, ":\n", e$message, "\n")
      stop(e)
    }
  )
}

## Root directory
root <- here()

## ------------------------------------------------------------------
## 0. Pre-flight check: required folders
## ------------------------------------------------------------------

req_dirs <- c(
  "data/raw",
  "data/interim",
  "data/validation",
  "outputs/validation/tables",
  "outputs/validation/plots",
  "codes"
)

for (d in req_dirs) {
  path <- file.path(root, d)
  if (!dir.exists(path)) {
    message("Creating missing directory: ", path)
    dir.create(path, recursive = TRUE, showWarnings = FALSE)
  }
}

## ------------------------------------------------------------------
## 1. Run scripts in correct SFC dependency order
## ------------------------------------------------------------------

scripts <- c(
  "codes/00_setup.R",
  "codes/00_build_anchor_1950.R",
  "codes/01_load_raw.R",
  "codes/02_build_Ig_pattern.R",
  "codes/03_build_Ig_2003.R",
  "codes/04_build_Kg_2003.R",
  "codes/05_build_Kn_2003.R",
  "codes/06_sfc_engine.R",
  "codes/07_sfc_audit_and_rates.R",
  "codes/09_splice_diagnostics.R",
  "codes/10_export_validation_materials.R"
)

for (s in scripts) {
  run_safe(here(s))
}

## ------------------------------------------------------------------
## 2. Completion message
## ------------------------------------------------------------------

message("\n==================================================")
message(" ALL TD–SFC PIPELINE SCRIPTS COMPLETED SUCCESSFULLY")
message(" Outputs available under: outputs/validation/")
message("==================================================\n")
