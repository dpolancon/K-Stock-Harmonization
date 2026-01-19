############################################################
## 07_sfc_audit_and_rates.R — TD–SFC COMPLIANT (Integrated)
##
## Purpose:
##   (A) Full SFC Identity Audit:
##        - Validate:
##            * Kg_t − Kg_{t−1} = Ig_t − R_t
##            * Kn_t − Kn_{t−1} = Ig_t − D_t
##            * Kn_t ≤ Kg_t  (net–gross ordering)
##        - Produce red-flag classifications + summaries
##
##   (B) Rate Diagnostics Summary:
##        - Summaries of δ, z, i, FNKF, Kn/Kg, SFC residual magnitudes
##        - Export sfc_rate_summary.rds for code 10
##
## Outputs → data/interim/ :
##     audit_SFC_panel_full.rds
##     audit_summary_residuals.rds
##     audit_summary_ordering.rds
##     sfc_rate_summary.rds
############################################################

library(dplyr)
library(tidyr)
library(here)

dir_int <- here("data","interim")

panel <- readRDS(file.path(dir_int, "panel_sfc_2003.rds"))

############################################################
## 1. CHECK REQUIRED STRUCTURE
############################################################

req <- c("year","asset","Ig","Kg","Kn",
         "dKg","dKn","D","R",
         "eps_Kg","eps_Kn","eps_joint",
         "Kn_over_Kg","flag_Kn_gt_Kg",
         "delta","z","i","FNKF")

if (!all(req %in% names(panel))) {
  stop("panel_sfc_2003.rds is missing required SFC columns. Re-run 06.")
}

############################################################
## 2. CLASSIFIER FOR RESIDUALS
############################################################

classify_residual <- function(x, tol_strict=1e-10, tol_soft=1e-6){
  dplyr::case_when(
    is.na(x)                     ~ "NA",
    abs(x) <= tol_strict         ~ "OK_strict",
    abs(x) <= tol_soft           ~ "OK_soft",
    abs(x) >  tol_soft           ~ "FLAG_large"
  )
}

############################################################
## 3. BUILD FULL AUDIT PANEL
############################################################

audit <- panel %>%
  mutate(
    epsKg_class = classify_residual(eps_Kg),
    epsKn_class = classify_residual(eps_Kn),
    epsJ_class  = classify_residual(eps_joint),
    ordering_flag = if_else(flag_Kn_gt_Kg, "Kn>Kg", "OK")
  ) %>%
  select(year, asset,
         eps_Kg, epsKg_class,
         eps_Kn, epsKn_class,
         eps_joint, epsJ_class,
         Kn_over_Kg, ordering_flag)

############################################################
## 4. SUMMARY TABLES (RESIDUALS + ORDERING)
############################################################

summary_eps <- audit %>%
  pivot_longer(
    cols = c(epsKg_class, epsKn_class, epsJ_class),
    names_to = "type",
    values_to = "class"
  ) %>%
  group_by(type, class) %>%
  summarise(n = n(), .groups = "drop") %>%
  arrange(type, class)

summary_ordering <- audit %>%
  count(ordering_flag)

############################################################
## 5. RATE SUMMARY (delta, z, i, FNKF, Kn/Kg, residual magnitudes)
############################################################

sfc_rate_summary <- panel %>%
  group_by(asset) %>%
  summarise(
    n_obs = n(),
    
    # ---- Depreciation δ ----
    delta_min  = min(delta, na.rm=TRUE),
    delta_p10  = quantile(delta, 0.10, na.rm=TRUE),
    delta_med  = median(delta, na.rm=TRUE),
    delta_mean = mean(delta, na.rm=TRUE),
    delta_p90  = quantile(delta, 0.90, na.rm=TRUE),
    delta_max  = max(delta, na.rm=TRUE),
    
    # ---- Depletion z ----
    z_min  = min(z, na.rm=TRUE),
    z_p10  = quantile(z, 0.10, na.rm=TRUE),
    z_med  = median(z, na.rm=TRUE),
    z_mean = mean(z, na.rm=TRUE),
    z_p90  = quantile(z, 0.90, na.rm=TRUE),
    z_max  = max(z, na.rm=TRUE),
    
    # ---- Investment–capital ratio i ----
    i_min = min(i, na.rm=TRUE),
    i_med = median(i, na.rm=TRUE),
    i_mean = mean(i, na.rm=TRUE),
    i_max = max(i, na.rm=TRUE),
    
    # ---- Net fixed capital formation ----
    FNKF_min = min(FNKF, na.rm=TRUE),
    FNKF_med = median(FNKF, na.rm=TRUE),
    FNKF_mean = mean(FNKF, na.rm=TRUE),
    FNKF_max = max(FNKF, na.rm=TRUE),
    
    # ---- Kn/Kg ----
    KnKg_min  = min(Kn / Kg, na.rm=TRUE),
    KnKg_med  = median(Kn / Kg, na.rm=TRUE),
    KnKg_mean = mean(Kn / Kg, na.rm=TRUE),
    KnKg_max  = max(Kn / Kg, na.rm=TRUE),
    
    # ---- SFC residual magnitudes ----
    epsKg_mean    = mean(abs(eps_Kg), na.rm=TRUE),
    epsKn_mean    = mean(abs(eps_Kn), na.rm=TRUE),
    epsJoint_mean = mean(abs(eps_joint), na.rm=TRUE)
  ) %>%
  ungroup()

############################################################
## 6. EXPORT ALL OBJECTS
############################################################

saveRDS(audit,            file.path(dir_int, "audit_SFC_panel_full.rds"))
saveRDS(summary_eps,      file.path(dir_int, "audit_summary_residuals.rds"))
saveRDS(summary_ordering, file.path(dir_int, "audit_summary_ordering.rds"))
saveRDS(sfc_rate_summary, file.path(dir_int, "sfc_rate_summary.rds"))

message("\n==============================")
message(" 07: SFC AUDIT + RATE SUMMARY DONE")
message("==============================")
message("Residual classifications exported.")
message("Net–gross ordering summary exported.")
message("Rate diagnostics summary exported (sfc_rate_summary.rds).")
message("==============================\n")
