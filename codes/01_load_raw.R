############################################################
## 01_load_raw.R — TD–SFC COMPLIANT VERSION
## Stock–flow consistent capital stock reconstruction (Chile)
############################################################

## -------------------------
## Libraries
## -------------------------
library(dplyr)
library(tidyr)
library(readxl)
library(stringr)
library(purrr)
library(here)

project_root <- here::here()
message("Project root detected: ", project_root)

## -------------------------
## Load project setup
## -------------------------
setup_file <- here::here("codes", "00_setup.R")
if (!file.exists(setup_file)) stop("00_setup.R not found.")
source(setup_file)

message("00_setup.R successfully loaded.\n")

## Canonical assets
canonical <- c("ME","NRC","RC","C","T","NR")

############################################################
## SAFE MAPPING FUNCTION (TD–SFC compliant)
############################################################

apply_mapping <- function(df, map) {
  
  map2 <- map %>% rename(canonical = asset, asset = original)
  
  out <- df %>%
    left_join(map2, by = "asset", relationship = "many-to-one") %>%
    mutate(asset = if_else(!is.na(canonical), canonical, asset)) %>%
    select(-canonical)
  
  leftovers <- out %>%
    filter(!asset %in% canonical) %>%
    pull(asset) %>% unique()
  
  if (length(leftovers) > 0) {
    warning("Unmapped assets detected (allowed but tracked): ",
            paste(leftovers, collapse = ", "))
  }
  
  return(out)
}

############################################################
## 1. Pérez–Eyzaguirre Aggregate Demand
############################################################

file_AD <- file.path(dir_data_raw, "PerezEyzaguirre_DemandaAgregada.xlsx")

raw_AD <- read_excel(file_AD) %>%
  rename(year = 1) %>% mutate(year = as.integer(year))

raw_AD_tidy <- raw_AD %>%
  pivot_longer(-year, names_to="var", values_to="value") %>%
  mutate(
    asset = NA_character_,
    price_base = "2003_CLP",
    source = "PerezEyzaguirre_AD"
  )

saveRDS(raw_AD_tidy, file.path(dir_data_interim, "raw_AD.rds"))

############################################################
## 2. Hofman 2000 — Gross Investment (Ig)
############################################################

map_hofman_Ig <- tribble(
  ~original,        ~asset,
  "Ig_ME_H2000",    "ME",
  "Ig_NRC_H2000",   "NRC",
  "Ig_RC_H2000",    "RC",
  "Ig_tot_H2000",   "T"
)

file_hofman_Ig <- file.path(dir_data_raw, "Hofman2000_GrossInvestment.xlsx")

raw_hofman_Ig <- read_excel(file_hofman_Ig) %>%
  rename(year = 1) %>% mutate(year = as.integer(year)) %>%
  pivot_longer(-year, names_to="asset", values_to="value") %>%
  mutate(
    var        = "Ig",
    price_base = "1980_CLP",
    source     = "Hofman2000_Ig"
  ) %>%
  apply_mapping(map_hofman_Ig) %>%
  arrange(year, asset)

saveRDS(raw_hofman_Ig, file.path(dir_data_interim, "raw_hofman_Ig.rds"))

############################################################
## 3. Hofman 2000 — Gross & Net Stocks
############################################################

map_hofman_K <- tribble(
  ~original, ~asset,
  "ME",      "ME",
  "C",       "C",
  "NRC",     "NRC",
  "RC",      "RC",
  "NR",      "NR",
  "T",       "T"
)

file_hofman_K <- file.path(dir_data_raw, "Hofman_Kstock_gross_net_19501994.xlsx")

raw_hofman_K <- map_dfr(
  excel_sheets(file_hofman_K),
  function(sht) {
    
    df <- read_excel(file_hofman_K, sheet=sht) %>%
      rename(year = 1) %>% mutate(year = as.integer(year)) %>%
      select(-any_of("Total"))
    
    df %>%
      pivot_longer(-year, names_to="asset", values_to="value") %>%
      mutate(
        var = case_when(
          str_to_lower(sht) == "kg" ~ "Kg",
          str_to_lower(sht) == "kn" ~ "Kn",
          TRUE ~ NA_character_
        ),
        price_base = "1980_CLP",
        source = "Hofman2000_K"
      ) %>%
      apply_mapping(map_hofman_K)
  }
) %>% arrange(year, var, asset)

saveRDS(raw_hofman_K, file.path(dir_data_interim, "raw_hofman_K.rds"))

############################################################
## 4. Clio-Lab — GFKF (real, nominal, Pk)
############################################################

file_clio_Ig <- file.path(dir_data_raw, "ClioLab_GFKF_Freal_nominal_Pk.xlsx")

raw_clio_Ig <- map_dfr(
  excel_sheets(file_clio_Ig),
  function(sht) {
    
    df <- read_excel(file_clio_Ig, sheet=sht) %>%
      rename(year = 1) %>% mutate(year = as.integer(year))
    
    df %>%
      pivot_longer(-year, names_to="asset", values_to="value") %>%
      mutate(
        var = sht,
        price_base = case_when(
          str_detect(str_to_lower(sht),"real") ~ "2003_CLP",
          str_detect(str_to_lower(sht),"nom")  ~ "current_CLP",
          str_detect(str_to_lower(sht),"pk")   ~ "index"
        ),
        source = "ClioLab_GFCF"
      )
  }
)

saveRDS(raw_clio_Ig, file.path(dir_data_interim, "raw_clio_Ig.rds"))

############################################################
## 5. Clio-Lab — Net Capital Stock (Kn)
############################################################

map_clio_Kn <- tribble(
  ~original,      ~asset,
  "Kn_C_CL",      "C",
  "Kn_ME",        "ME",
  "K_net_tot_CL", "T"
)

file_clio_Kn <- file.path(dir_data_raw, "Kn_ClioLab.xlsx")

raw_clio_Kn <- read_excel(file_clio_Kn) %>%
  rename(year = 1) %>% mutate(year = as.integer(year)) %>%
  pivot_longer(-year, names_to="asset", values_to="value") %>%
  mutate(
    var="Kn",
    price_base="2003_CLP",
    source="ClioLab_Kn"
  ) %>%
  apply_mapping(map_clio_Kn)

saveRDS(raw_clio_Kn, file.path(dir_data_interim, "raw_clio_Kn.rds"))

raw_cliolab <- bind_rows(raw_clio_Ig, raw_clio_Kn)
saveRDS(raw_cliolab, file.path(dir_data_interim, "raw_cliolab.rds"))

############################################################
## 6. Tafunell 2013 — Ig index
############################################################

# Correct mapping for your actual file columns:
# year, Ig_ME, Ig_NRC, Ig_tot
map_tafunell_2013 <- tribble(
  ~original, ~asset,
  "Ig_ME",   "ME",
  "Ig_NRC",  "NRC",
  "Ig_tot",  "T"
)

file_taf_Ig <- file.path(dir_data_raw, "tafunel_2013_Ig.xlsx")

raw_tafunell_Ig <- read_excel(file_taf_Ig) %>%
  rename(year = 1) %>%
  mutate(year = as.integer(year)) %>%
  pivot_longer(-year, names_to = "asset", values_to = "value") %>%
  mutate(
    var        = "Ig_index",
    price_base = "index",
    source     = "Tafunell2013_Ig"
  ) %>%
  apply_mapping(map_tafunell_2013)

# FAIL FAST if anything didn’t map into the canonical taxonomy
unmapped_taf <- raw_tafunell_Ig %>%
  filter(!asset %in% canonical) %>%
  distinct(asset) %>%
  pull(asset)

if (length(unmapped_taf) > 0) {
  stop(
    "Tafunell 2013 contains unmapped assets: ",
    paste(unmapped_taf, collapse = ", "),
    ". Fix map_tafunell_2013 before proceeding."
  )
}

saveRDS(raw_tafunell_Ig, file.path(dir_data_interim, "raw_tafunell_Ig.rds"))
message("Tafunell 2013 loaded and mapped correctly.")

############################################################
## 7. Tafunell–Ducoing 2016 — Kg index
############################################################

map_td_2016 <- tribble(
  ~original, ~asset,
  "Kg_C",    "C",
  "Kg_NR",   "NR",
  "Kg_RC",   "RC",
  "Kg_T",    "T",
  "Kg_ME",   "ME",
  "Kg_NRC",  "NRC"
)

file_TD_Kg <- file.path(dir_data_raw, "Tafunell_Ducoing_2016_Kg.xlsx")

raw_TD_indices <- read_excel(file_TD_Kg) %>%
  rename(year=1) %>% mutate(year = as.integer(year)) %>%
  pivot_longer(-year, names_to="asset", values_to="value") %>%
  mutate(
    var="Kg_index",
    price_base="index_1929_100",
    source="TafunellDucoing2016_Kg"
  ) %>%
  apply_mapping(map_td_2016)

saveRDS(raw_TD_indices, file.path(dir_data_interim, "raw_TD_indices.rds"))

############################################################
## END — Script 01 successfully ingested and standardized.
message("01_load_raw.R ingested, validated, and TD–SFC compliant.")
############################################################
