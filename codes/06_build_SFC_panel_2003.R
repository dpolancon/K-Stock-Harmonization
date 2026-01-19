############################################################
## 06_build_SFC_panel_2003.R — Master Panel Assembly (NO derivation)
## Stock–flow consistent capital stock reconstruction (Chile)
##
## Purpose:
##   - Assemble one canonical long panel in 2003 CLP:
##       Ig_2003  (flow, by asset)
##       Kg_2003  (gross stock, by asset)
##       Kn_2003  (net stock, by asset)
##   - Enforce SFC identities via additivity checks (audit only).
##   - Enforce physical consistency: Kn <= Kg (audit only).
##   - Save: data/interim/sfc_panel_2003_1900_1994.rds
##
## Notes:
##   - This script does NOT reconstruct by accumulation.
##   - It just consolidates consistent series into one canonical object.
############################################################

library(dplyr)
library(tidyr)
library(here)

source(here("codes","00_setup.R"))

dir_int <- here("data","interim")

# -------------------------
# Local helper: additivity
# -------------------------
check_additivity <- function(df_long, var_name) {
  wide <- df_long %>%
    filter(var == var_name, asset %in% c("ME","NRC","RC","C","NR","T")) %>%
    select(year, asset, value) %>%
    pivot_wider(names_from = asset, values_from = value)
  
  out <- wide %>%
    mutate(
      res_C  = C  - (NRC + RC),
      res_NR = NR - (ME  + NRC),
      res_T  = T  - (ME  + NRC + RC),
      max_abs_res = pmax(abs(res_C), abs(res_NR), abs(res_T), na.rm = TRUE)
    ) %>%
    transmute(year, res_C, res_NR, res_T, max_abs_res)
  
  message(var_name, " additivity check — max |residual| = ",
          format(max(out$max_abs_res, na.rm = TRUE), scientific = TRUE))
  
  out
}

# -------------------------
# 1) Load canonical series
# -------------------------
Ig <- readRDS(file.path(dir_int, "Ig_2003.rds")) %>%
  mutate(dataset = "Ig_2003")

Kg <- readRDS(file.path(dir_int, "Kg_2003.rds")) %>%
  mutate(dataset = "Kg_2003")

Kn <- readRDS(file.path(dir_int, "Kn_2003.rds")) %>%
  mutate(dataset = "Kn_2003")

# Basic schema checks
req <- c("year","asset","value","var","price_base","source")
stopifnot(all(req %in% names(Ig)),
          all(req %in% names(Kg)),
          all(req %in% names(Kn)))

# -------------------------
# 2) Harmonize and bind
# -------------------------
panel <- bind_rows(Ig, Kg, Kn) %>%
  filter(year >= 1900, year <= 1994) %>%
  mutate(
    year = as.integer(year),
    asset = as.character(asset),
    var = as.character(var),
    price_base = as.character(price_base)
  ) %>%
  arrange(var, asset, year)

# -------------------------
# 3) Coverage audits
# -------------------------
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
print(cov)

assets_by_year <- panel %>%
  filter(var %in% c("Ig","Kg","Kn")) %>%
  group_by(var, year) %>%
  summarise(n_assets = n_distinct(asset), .groups="drop") %>%
  group_by(var) %>%
  summarise(min_assets = min(n_assets), max_assets = max(n_assets), .groups="drop")
print(assets_by_year)

# -------------------------
# 4) Additivity audits
# -------------------------
Ig_add <- check_additivity(panel, "Ig")
Kg_add <- check_additivity(panel, "Kg")
Kn_add <- check_additivity(panel, "Kn")

saveRDS(Ig_add, file.path(dir_int, "Ig_additivity_masterpanel.rds"))
saveRDS(Kg_add, file.path(dir_int, "Kg_additivity_masterpanel.rds"))
saveRDS(Kn_add, file.path(dir_int, "Kn_additivity_masterpanel.rds"))

# -------------------------
# 5) Physical consistency: Kn <= Kg
# -------------------------
panel_K <- panel %>%
  filter(var %in% c("Kg","Kn"), asset %in% c("ME","NRC","RC","C","NR","T")) %>%
  select(year, asset, var, value) %>%
  pivot_wider(names_from = var, values_from = value)

viol <- panel_K %>%
  mutate(gap = Kn - Kg, viol = Kn > Kg + 1e-8) %>%
  filter(viol)

cat("\nKn <= Kg violations:", nrow(viol), "\n")
if (nrow(viol) > 0) {
  print(viol %>% arrange(desc(gap)) %>% slice_head(n=20))
} else {
  cat("[OK] No Kn > Kg violations.\n")
}

# -------------------------
# 6) Save canonical master panel
# -------------------------
saveRDS(panel, file.path(dir_int, "sfc_panel_2003_1900_1994.rds"))
message(">>> 06_build_SFC_panel_2003.R completed: saved sfc_panel_2003_1900_1994.rds")
