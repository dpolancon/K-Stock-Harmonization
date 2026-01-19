############################################################
## 07_diagnostics.R — Freeze diagnostic snapshot
## Purpose:
##  - Save a frozen snapshot of the canonical panel + audits
##  - Create a manifest with metadata to make it reproducible
##  - DOES NOT modify Ig/Kg/Kn series
############################################################

library(dplyr)
library(tidyr)
library(here)
library(digest)

source(here("codes","00_setup.R"))
dir_int <- here("data","interim")
dir_diag <- here("data","diagnostics")
dir.create(dir_diag, showWarnings = FALSE, recursive = TRUE)

# -------------------------
# 1) Load canonical master panel
# -------------------------
panel <- readRDS(file.path(dir_int, "sfc_panel_2003_1900_1994.rds"))

# -------------------------
# 2) Recompute key audits (so the freeze is self-contained)
# -------------------------

# 2.1 Duplicate cells
dup_cells <- panel %>% count(year, asset, var) %>% filter(n > 1)

# 2.2 Coverage
cov <- panel %>%
  group_by(var) %>%
  summarise(
    min_year = min(year),
    max_year = max(year),
    n_years  = n_distinct(year),
    n_rows   = n(),
    n_na     = sum(is.na(value)),
    .groups = "drop"
  )

assets_by_year <- panel %>%
  filter(var %in% c("Ig","Kg","Kn")) %>%
  group_by(var, year) %>%
  summarise(n_assets = n_distinct(asset), .groups="drop") %>%
  group_by(var) %>%
  summarise(min_assets = min(n_assets), max_assets = max(n_assets), .groups="drop")

# 2.3 Additivity (local helper)
check_additivity <- function(df_long, var_name) {
  wide <- df_long %>%
    filter(var == var_name, asset %in% c("ME","NRC","RC","C","NR","T")) %>%
    select(year, asset, value) %>%
    pivot_wider(names_from = asset, values_from = value)
  
  wide %>%
    mutate(
      res_C  = C  - (NRC + RC),
      res_NR = NR - (ME  + NRC),
      res_T  = T  - (ME  + NRC + RC),
      max_abs_res = pmax(abs(res_C), abs(res_NR), abs(res_T), na.rm = TRUE)
    ) %>%
    transmute(year, res_C, res_NR, res_T, max_abs_res)
}

Ig_add <- check_additivity(panel, "Ig")
Kg_add <- check_additivity(panel, "Kg")
Kn_add <- check_additivity(panel, "Kn")

# 2.4 Physical consistency Kn <= Kg
panel_K <- panel %>%
  filter(var %in% c("Kg","Kn"), asset %in% c("ME","NRC","RC","C","NR","T")) %>%
  select(year, asset, var, value) %>%
  pivot_wider(names_from = var, values_from = value) %>%
  mutate(gap = Kn - Kg, viol = Kn > Kg + 1e-8)

viol_Kn_gt_Kg <- panel_K %>% filter(viol)

# 2.5 Boundary jumps 1949->1950 (for key assets)
boundary_check <- panel %>%
  filter(year %in% c(1949,1950),
         asset %in% c("ME","NRC","RC","C","T"),
         var %in% c("Ig","Kg","Kn")) %>%
  select(year, var, asset, value) %>%
  pivot_wider(names_from = year, values_from = value) %>%
  mutate(log_jump = log(`1950`) - log(`1949`)) %>%
  arrange(var, asset)

boundary_summary <- summary(boundary_check$log_jump)

# 2.6 i_proxy diagnostics (NOT a definition, just diagnostic)
panel_w <- panel %>%
  filter(asset %in% c("ME","NRC","RC","T")) %>%
  select(year, asset, var, value) %>%
  pivot_wider(names_from = var, values_from = value) %>%
  arrange(asset, year) %>%
  group_by(asset) %>%
  mutate(i_proxy = Ig / lag(Kg)) %>%
  ungroup()

i_proxy_stats <- panel_w %>%
  group_by(asset) %>%
  summarise(
    min_i = min(i_proxy, na.rm=TRUE),
    p5_i  = quantile(i_proxy, 0.05, na.rm=TRUE),
    med_i = median(i_proxy, na.rm=TRUE),
    p95_i = quantile(i_proxy, 0.95, na.rm=TRUE),
    max_i = max(i_proxy, na.rm=TRUE),
    .groups="drop"
  )

i_proxy_top5 <- panel_w %>%
  group_by(asset) %>%
  slice_max(i_proxy, n = 5, with_ties = FALSE) %>%
  ungroup() %>%
  select(asset, year, i_proxy, Ig, Kg) %>%
  arrange(asset, desc(i_proxy))

# -------------------------
# 3) Freeze bundle (single RDS)
# -------------------------

stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
freeze_name <- paste0("freeze_diag_sfc_2003_1900_1994_", stamp)
freeze_path <- file.path(dir_diag, paste0(freeze_name, ".rds"))

bundle <- list(
  meta = list(
    created_at = Sys.time(),
    project_root = here::here(),
    object_name = freeze_name
  ),
  panel = panel,
  audits = list(
    dup_cells = dup_cells,
    cov = cov,
    assets_by_year = assets_by_year,
    additivity = list(Ig = Ig_add, Kg = Kg_add, Kn = Kn_add),
    Kn_le_Kg = list(violations = viol_Kn_gt_Kg, full = panel_K),
    boundary = list(table = boundary_check, summary = boundary_summary),
    i_proxy = list(stats = i_proxy_stats, top5 = i_proxy_top5)
  )
)

saveRDS(bundle, freeze_path)

# Hash for integrity
hash <- digest::digest(file = freeze_path, algo = "sha256")

manifest <- tibble(
  freeze_file = basename(freeze_path),
  sha256 = hash,
  n_rows_panel = nrow(panel),
  min_year = min(panel$year),
  max_year = max(panel$year),
  created_at = as.character(Sys.time())
)

write_csv(manifest, file.path(dir_diag, paste0(freeze_name, "_MANIFEST.csv")))

message("FROZEN DIAGNOSTICS SAVED:")
message(" - RDS: ", freeze_path)
message(" - Manifest: ", file.path(dir_diag, paste0(freeze_name, "_MANIFEST.csv")))
message(" - SHA256: ", hash)
