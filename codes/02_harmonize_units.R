############################################################
## 02_harmonize_units.R — TD–SFC COMPLIANT VERSION (FINAL)
##
## Objetivo:
##   - Construir Ig_2003_pattern.rds  (único nivel = Pérez-E)
##   - Construir Kg_pattern.rds       (Tafunell–Ducoing solo shares)
##   - Construir Kn_2003_levels.rds   (Clio-Lab, con corrección de escala)
##
## Este script NO produce series finales.
## Solo produce patrones (Ig, Kg) y niveles (Kn).
############################################################

library(dplyr)
library(tidyr)
library(purrr)
library(readr)
library(here)

dir_int <- here("data","interim")
dir_out <- here("data","interim")

canonical <- c("ME","NRC","RC","C","T","NR")

############################################################
## 1. Cargar raw datasets
############################################################

AD       <- readRDS(file.path(dir_int, "raw_AD.rds"))
hof_Ig   <- readRDS(file.path(dir_int, "raw_hofman_Ig.rds"))
hof_K    <- readRDS(file.path(dir_int, "raw_hofman_K.rds"))
clio_Kn  <- readRDS(file.path(dir_int, "raw_clio_Kn.rds"))
taf_Ig   <- readRDS(file.path(dir_int, "raw_tafunell_Ig.rds"))
td_Kg    <- readRDS(file.path(dir_int, "raw_TD_indices.rds"))

############################################################
## 2. Extract Pérez–Eyzaguirre Ig levels (ABSOLUTE BENCHMARK)
##    Keep ME and C separate (do NOT sum them here)
############################################################

Ig_perez <- AD %>%
  filter(var %in% c("FBKF en maquinaria", "FBKF en construcción")) %>%
  mutate(asset = case_when(
    var == "FBKF en maquinaria"   ~ "ME",
    var == "FBKF en construcción" ~ "C",
    TRUE ~ NA_character_
  )) %>%
  select(year, asset, value) %>%
  tidyr::pivot_wider(names_from = asset, values_from = value, names_prefix = "Ig_")

stopifnot(all(c("Ig_ME","Ig_C") %in% names(Ig_perez)))

############################################################
## 3. Build NRC/RC split inside Construction using patterns
##    IMPORTANT: Use Hofman ONLY.
##    Tafunell columns are indices / non-additive → do NOT use residual RC.
############################################################

shareC <- hof_Ig %>%
  filter(asset %in% c("NRC","RC")) %>%
  group_by(year) %>%
  summarise(
    NRC = sum(value[asset=="NRC"], na.rm = TRUE),
    RC  = sum(value[asset=="RC"],  na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    C = NRC + RC,
    share_NRC_in_C = if_else(C > 0, NRC / C, NA_real_)
  ) %>%
  select(year, share_NRC_in_C)

## Optional: fill gaps if any (usually not needed if Hofman covers all years you use)
shareC <- shareC %>%
  arrange(year) %>%
  tidyr::fill(share_NRC_in_C, .direction = "downup")


############################################################
## 4. Construct Ig_2003_pattern (NOT final Ig, but TD–SFC consistent)
##    Anchor ME and C to Pérez-E, split C into NRC/RC via shareC
############################################################

Ig_2003_pattern <- Ig_perez %>%
  left_join(shareC, by = "year") %>%
  mutate(
    share_NRC_in_C = if_else(is.na(share_NRC_in_C), 0.5, share_NRC_in_C), # safe fallback
    Ig_NRC = share_NRC_in_C * Ig_C,
    Ig_RC  = (1 - share_NRC_in_C) * Ig_C,
    Ig_T   = Ig_ME + Ig_C,
    Ig_NR  = Ig_ME + Ig_NRC
  ) %>%
  select(year, Ig_ME, Ig_C, Ig_NRC, Ig_RC, Ig_T, Ig_NR) %>%
  tidyr::pivot_longer(-year, names_to = "asset", values_to = "value") %>%
  mutate(
    asset = sub("^Ig_", "", asset),
    var = "Ig_2003_pattern",
    price_base = "2003_CLP",
    source = "PerezEyzaguirre levels + Hofman NRC/RC split"
  ) %>%
  select(year, asset, var, value, price_base, source)

saveRDS(Ig_2003_pattern, file.path(dir_out, "Ig_2003_pattern.rds"))


############################################################
## 5. Kg patterns from Tafunell–Ducoing 2016
##    SOLO SHARES — nunca niveles
############################################################

Kg_pattern <- td_Kg %>%
  select(year, asset, value) %>%
  group_by(year) %>%
  mutate(share = value / sum(value)) %>%
  ungroup() %>%
  mutate(
    var = "Kg_pattern",
    price_base = "index_2019_100",
    source = "TafunellDucoing2016"
  )

saveRDS(Kg_pattern, file.path(dir_out, "Kg_pattern.rds"))

############################################################
## 6. Kn levels from Clio-Lab
##    CORRECCIÓN DE ESCALA: Clio suele estar en miles de millones.
############################################################

detect_scale <- function(x) {
  # Si la mediana es > 500 → casi seguro miles de millones
  if (median(x, na.rm = TRUE) > 500) return(1000)
  return(1)
}

scale_factor <- detect_scale(clio_Kn$value)

Kn_2003_levels <- clio_Kn %>%
  mutate(
    value = value * scale_factor,     # ← FIX CRÍTICO
    var = "Kn_2003_level",
    price_base = "2003_CLP",
    source = paste0("ClioLab_scaled_x", scale_factor)
  ) %>%
  select(year, asset, var, value, price_base, source)

saveRDS(Kn_2003_levels, file.path(dir_out, "Kn_2003_levels.rds"))

############################################################
## END — Script 02 TD–SFC compliant
message("02_harmonize_units.R completed.")
message(paste0("Clio Kn scale factor applied: x", scale_factor, 
               " (rule: median(Kn) > 500 => x1000)."))
message(paste0("Clio Kn median before scaling = ",
               format(median(clio_Kn$value, na.rm = TRUE), scientific = TRUE)))
############################################################
