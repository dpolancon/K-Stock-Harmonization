############################################################
## 08_sfc_implicit_2003.R — Implied magnitudes & rates (READ-ONLY)
## Project: Stock–Flow Consistent Capital Stock Reconstruction (Chile)
##
## Purpose:
##  - Load canonical panel: sfc_panel_2003_1900_1994.rds
##  - Assert it matches the latest frozen diagnostics snapshot (SHA256 guardrail)
##  - Compute implied magnitudes (dKg, dKn, D, R) and implied rates (delta, z, i)
##    using lagged denominators
##  - Create flags + compact audit tables (NO edits to Ig/Kg/Kn)
##  - Save:
##      data/processed/sfc_implicit_2003_1900_1994.rds
##      data/diagnostics/implicit_audit_YYYYmmdd_HHMMSS.rds
############################################################

suppressWarnings({
  library(dplyr)
  library(tidyr)
  library(here)
  library(readr)
  library(digest)
})

source(here("codes","00_setup.R"))  # dirs (dir_data_interim, processed), etc.

dir_int  <- here("data","interim")
dir_diag <- here("data","diagnostics")
dir_out  <- here("data","processed")

dir.create(dir_diag, showWarnings = FALSE, recursive = TRUE)
dir.create(dir_out,  showWarnings = FALSE, recursive = TRUE)

# ---------------------------------------------------------
# 0) Locate latest freeze + verify canonical panel hash
# ---------------------------------------------------------
panel_path <- file.path(dir_int, "sfc_panel_2003_1900_1994.rds")
stopifnot(file.exists(panel_path))

# Helper: pick latest manifest for freeze files (by filename timestamp)
manifest_files <- list.files(dir_diag, pattern = "freeze_diag_sfc_2003_1900_1994_.*_MANIFEST\\.csv$", full.names = TRUE)
if (length(manifest_files) == 0) {
  stop("No freeze manifest found in data/diagnostics. Run 07_diagnostics.R first.")
}
latest_manifest <- manifest_files[order(manifest_files, decreasing = TRUE)][1]

manifest <- readr::read_csv(latest_manifest, show_col_types = FALSE)
stopifnot(nrow(manifest) == 1, all(c("sha256","freeze_file") %in% names(manifest)))

# Compute current panel sha
panel_sha <- digest::digest(file = panel_path, algo = "sha256")

# The freeze sha in manifest is for the freeze RDS, not the panel itself.
# So we verify by loading the freeze bundle and hashing its embedded panel data too.
freeze_rds_path <- file.path(dir_diag, manifest$freeze_file)
if (!file.exists(freeze_rds_path)) {
  stop("Freeze RDS referenced in manifest not found: ", freeze_rds_path)
}

freeze_bundle <- readRDS(freeze_rds_path)
if (!("panel" %in% names(freeze_bundle))) stop("Freeze bundle does not contain $panel.")

# Hash the serialized frozen panel object (object hash, not file hash)
frozen_panel_obj_sha <- digest::digest(freeze_bundle$panel, algo = "sha256")

# Hash the current panel object too (object hash)
panel_obj <- readRDS(panel_path)
current_panel_obj_sha <- digest::digest(panel_obj, algo = "sha256")

if (current_panel_obj_sha != frozen_panel_obj_sha) {
  stop(
    "GUARDRAIL FAILED: current canonical panel object does NOT match frozen diagnostics snapshot.\n",
    " - current panel object sha256: ", current_panel_obj_sha, "\n",
    " - frozen panel  object sha256: ", frozen_panel_obj_sha, "\n",
    "This means upstream series changed. Re-freeze diagnostics (07) or restore baseline."
  )
}

message("Guardrail OK: canonical panel matches latest frozen snapshot.")
message(" - Latest freeze manifest: ", basename(latest_manifest))
message(" - Panel file sha256: ", panel_sha)

# ---------------------------------------------------------
# 1) Wide form by (year, asset): Ig, Kg, Kn
# ---------------------------------------------------------
req <- c("year","asset","var","value")
stopifnot(all(req %in% names(panel_obj)))

wide <- panel_obj %>%
  filter(var %in% c("Ig","Kg","Kn"),
         asset %in% c("ME","NRC","RC","C","NR","T")) %>%
  select(year, asset, var, value) %>%
  distinct(year, asset, var, value) %>%
  pivot_wider(names_from = var, values_from = value) %>%
  arrange(asset, year)

stopifnot(all(c("Ig","Kg","Kn") %in% names(wide)))

# ---------------------------------------------------------
# 2) Safe division (lagged denominators)
# ---------------------------------------------------------
safe_div <- function(num, denom, tol = 0) {
  dplyr::if_else(!is.na(denom) & abs(denom) > tol, num / denom, NA_real_)
}

# ---------------------------------------------------------
# 3) Compute implied magnitudes & rates (READ-ONLY)
# ---------------------------------------------------------
implicit <- wide %>%
  group_by(asset) %>%
  arrange(year, .by_group = TRUE) %>%
  mutate(
    Kg_lag = lag(Kg),
    Kn_lag = lag(Kn),
    
    dKg = Kg - Kg_lag,
    dKn = Kn - Kn_lag,
    
    # Implied flows from identities:
    # Kn_t - Kn_{t-1} = Ig_t - D_t  => D_t = Ig_t - dKn
    # Kg_t - Kg_{t-1} = Ig_t - R_t  => R_t = Ig_t - dKg
    D = Ig - dKn,
    R = Ig - dKg,
    
    # Rates with lagged denominators:
    delta = safe_div(D, Kn_lag),
    z     = safe_div(R, Kg_lag),
    i     = safe_div(Ig, Kg_lag),
    
    Kn_over_Kg = safe_div(Kn, Kg),
    
    # Residual sanity (should be ~0 by construction if formulas consistent)
    eps_Kn = dKn - (Ig - D),
    eps_Kg = dKg - (Ig - R),
    
    # Cross-check relation:
    # D - R = (Ig - dKn) - (Ig - dKg) = dKg - dKn
    eps_DR = (D - R) - (dKg - dKn)
  ) %>%
  ungroup() %>%
  mutate(
    period = case_when(
      year <= 1949 ~ "1900_1949",
      year <= 1994 ~ "1950_1994",
      TRUE ~ "other"
    ),
    
    # Flags (diagnostic, not edits)
    flag_Kn_gt_Kg = !is.na(Kn) & !is.na(Kg) & (Kn > Kg + 1e-8),
    
    # "Suspicious" implied values (tune thresholds later, just flags)
    flag_delta_gt_25pct = !is.na(delta) & (delta > 0.25),
    flag_z_gt_25pct     = !is.na(z)     & (z     > 0.25),
    flag_i_gt_25pct     = !is.na(i)     & (i     > 0.25),
    
    flag_D_negative = !is.na(D) & (D < 0),
    flag_R_negative = !is.na(R) & (R < 0)
  )

# ---------------------------------------------------------
# 4) Audits summary tables (compact)
# ---------------------------------------------------------
audit_rates_summary <- implicit %>%
  filter(year >= 1900, year <= 1994) %>%
  group_by(asset) %>%
  summarise(
    # core stats for rates
    delta_med = median(delta, na.rm = TRUE),
    delta_p95 = quantile(delta, 0.95, na.rm = TRUE),
    z_med     = median(z, na.rm = TRUE),
    z_p95     = quantile(z, 0.95, na.rm = TRUE),
    i_med     = median(i, na.rm = TRUE),
    i_p95     = quantile(i, 0.95, na.rm = TRUE),
    
    # counts of flags
    n_flag_Kn_gt_Kg     = sum(flag_Kn_gt_Kg, na.rm = TRUE),
    n_flag_delta_gt_25  = sum(flag_delta_gt_25pct, na.rm = TRUE),
    n_flag_z_gt_25      = sum(flag_z_gt_25pct, na.rm = TRUE),
    n_flag_i_gt_25      = sum(flag_i_gt_25pct, na.rm = TRUE),
    n_flag_D_negative   = sum(flag_D_negative, na.rm = TRUE),
    n_flag_R_negative   = sum(flag_R_negative, na.rm = TRUE),
    
    .groups = "drop"
  )

audit_eps <- implicit %>%
  summarise(
    max_abs_eps_Kn = max(abs(eps_Kn), na.rm = TRUE),
    max_abs_eps_Kg = max(abs(eps_Kg), na.rm = TRUE),
    max_abs_eps_DR = max(abs(eps_DR), na.rm = TRUE)
  )

# Boundary focus: 1949->1950 implied-rate jumps
audit_boundary <- implicit %>%
  filter(year %in% c(1949,1950), asset %in% c("ME","NRC","RC","C","T","NR")) %>%
  select(year, asset, delta, z, i, D, R, dKn, dKg) %>%
  pivot_wider(names_from = year, values_from = c(delta,z,i,D,R,dKn,dKg), names_sep = "_") %>%
  mutate(
    jump_delta = delta_1950 - delta_1949,
    jump_z     = z_1950     - z_1949,
    jump_i     = i_1950     - i_1949
  )

# ---------------------------------------------------------
# 5) Save outputs
# ---------------------------------------------------------
stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")

implicit_out_path <- file.path(dir_out, "sfc_implicit_2003_1900_1994.rds")
saveRDS(implicit, implicit_out_path)

audit_bundle <- list(
  meta = list(
    created_at = Sys.time(),
    canonical_panel_path = panel_path,
    canonical_panel_file_sha256 = panel_sha,
    latest_freeze_manifest = basename(latest_manifest),
    latest_freeze_file = basename(freeze_rds_path),
    canonical_panel_object_sha256 = current_panel_obj_sha,
    frozen_panel_object_sha256 = frozen_panel_obj_sha
  ),
  audits = list(
    rates_summary = audit_rates_summary,
    eps_summary   = audit_eps,
    boundary      = audit_boundary
  )
)

audit_path <- file.path(dir_diag, paste0("implicit_audit_", stamp, ".rds"))
saveRDS(audit_bundle, audit_path)

message(">>> 08_sfc_implicit_2003.R completed.")
message(" - Implied panel saved: ", implicit_out_path)
message(" - Audit bundle saved:  ", audit_path)
