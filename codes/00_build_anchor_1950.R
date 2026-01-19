############################################################
## 00_build_anchor_1950.R — Anchor Construction (Hofman 1950)
## Project: Stock–Flow Consistent Capital Stock Reconstruction (Chile)
##
## Purpose:
##   - Build the 1950 anchor levels for gross (Kg) and net (Kn) capital stocks
##     by asset, using Hofman (2000) as the unique stock-level benchmark.
##   - Express anchors in:
##       (a) Hofman constant 1980 CLP (as provided)
##       (b) Constant 2003 CLP (rebased using Clio-Lab Pk index, 2003=100)
##   - Enforce SFC-consistent aggregates:
##       C  = NRC + RC
##       NR = ME  + NRC
##       T  = ME  + NRC + RC
##   - Run integrity checks and export: data/interim/anchor_1950.rds
##
## Critical unit convention (explicit):
##   - This script ASSUMES Hofman stock levels are already expressed in
##     "millions of 1980 CLP" (a very common convention in historical accounts).
##   - Therefore: NO extra /1e6 conversion is performed.
##   - If you later confirm Hofman is in pesos (not millions), change
##     HOFMAN_UNIT_MULT below to 1e-6 accordingly (and re-run audit).
##
## Price-base logic:
##   - Hofman is constant 1980 CLP (a real series).
##   - To convert constant-1980 values into constant-2003 values, we change
##     the base using ONE fixed factor: 100 / Pk_1980.
##   - Do NOT use Pk_1950 for this conversion (that would imply nominal→real).
##
## Run order:
##   - Run 00_setup.R first (for paths + packages + file names).
##   - Then run this script.
############################################################

suppressWarnings({
  library(dplyr)
  library(tidyr)
  library(readxl)
  library(stringr)
  library(here)
})

## ---------------------------------------------------------
## 1. Load setup (paths + file locations)
## ---------------------------------------------------------
setup_file <- here::here("codes", "00_setup.R")
if (!file.exists(setup_file)) stop("00_setup.R not found at codes/00_setup.R")
source(setup_file)

## Safety: ensure required file paths exist (defined in 00_setup.R)
stopifnot(exists("file_hof_K"), exists("file_clioPk"),
          exists("dir_data_interim"))

## ---------------------------------------------------------
## 2. User-controlled knob: Hofman unit scaling
## ---------------------------------------------------------
## Default assumption: Hofman levels are already in "millions of 1980 CLP"
HOFMAN_UNIT_LABEL <- "Hofman_1980_CLP_millions"
HOFMAN_UNIT_MULT  <- 1

## If you later confirm Hofman is in pesos (NOT millions), set:
## HOFMAN_UNIT_LABEL <- "Hofman_1980_CLP_pesos"
## HOFMAN_UNIT_MULT  <- 1e-6
##
## If you confirm Hofman is in thousands of millions (rare), set:
## HOFMAN_UNIT_LABEL <- "Hofman_1980_CLP_thousands_of_millions"
## HOFMAN_UNIT_MULT  <- 1000

## ---------------------------------------------------------
## 3. Load Hofman (2000) gross and net stocks (constant 1980 CLP)
## ---------------------------------------------------------
hof_Kg_1980 <- read_excel(file_hof_K, sheet = "Kg") %>%
  rename(year = 1L) %>%
  mutate(year = as.integer(year))

hof_Kn_1980 <- read_excel(file_hof_K, sheet = "Kn") %>%
  rename(year = 1L) %>%
  mutate(year = as.integer(year))

## Extract 1950 rows
hof_Kg_1950 <- hof_Kg_1980 %>% filter(year == 1950)
hof_Kn_1950 <- hof_Kn_1980 %>% filter(year == 1950)

if (nrow(hof_Kg_1950) != 1L | nrow(hof_Kn_1950) != 1L) {
  stop("Expected exactly one row for year 1950 in Hofman Kg and Kn sheets.")
}

## Drop any “Total” columns (we rebuild aggregates explicitly)
drop_cols <- intersect(names(hof_Kg_1950), c("Total","TOTAL","Tot","tot"))
hof_Kg_1950 <- hof_Kg_1950 %>% select(-all_of(drop_cols))
hof_Kn_1950 <- hof_Kn_1950 %>% select(-all_of(drop_cols))

## Coerce numerics safely (in case Excel read as character with commas)
as_num_safe <- function(x) suppressWarnings(as.numeric(gsub(",", ".", x)))

hof_Kg_1950 <- hof_Kg_1950 %>%
  mutate(across(where(is.character), as_num_safe))

hof_Kn_1950 <- hof_Kn_1950 %>%
  mutate(across(where(is.character), as_num_safe))

## ---------------------------------------------------------
## 4. Build SFC-consistent components and aggregates (1980 base)
## ---------------------------------------------------------
get_MENRC <- function(df) {
  tibble(
    year = df$year,
    ME   = df$ME,
    NRC  = df$NRC,
    RC   = df$RC
  )
}

Kg_MENRC <- get_MENRC(hof_Kg_1950)
Kn_MENRC <- get_MENRC(hof_Kn_1950)

Kg_1950_1980 <- Kg_MENRC %>%
  mutate(
    C  = NRC + RC,
    NR = ME  + NRC,
    T  = ME  + NRC + RC
  ) %>%
  select(year, ME, C, NRC, RC, T, NR) %>%
  mutate(across(-year, ~ .x * HOFMAN_UNIT_MULT))

Kn_1950_1980 <- Kn_MENRC %>%
  mutate(
    C  = NRC + RC,
    NR = ME  + NRC,
    T  = ME  + NRC + RC
  ) %>%
  select(year, ME, C, NRC, RC, T, NR) %>%
  mutate(across(-year, ~ .x * HOFMAN_UNIT_MULT))

## ---------------------------------------------------------
## 5. Load Clio-Lab Pk index (2003 = 100) and compute base-change factor
## ---------------------------------------------------------
clio_Pk <- read_excel(file_clioPk, sheet = "ig_nom_ig_real_Pk") %>%
  rename(year = 1L) %>%
  mutate(year = as.integer(year))

Pk_2003 <- clio_Pk %>% filter(year == 2003) %>% pull(Pk)
Pk_1980 <- clio_Pk %>% filter(year == 1980) %>% pull(Pk)

if (length(Pk_2003) != 1L) stop("Could not uniquely identify Pk for 2003.")
if (length(Pk_1980) != 1L) stop("Could not uniquely identify Pk for 1980.")

if (abs(Pk_2003 - 100) > 1e-6) {
  warning("Pk_2003 is not exactly 100. Check Clio-Lab Pk source.")
}

## Constant-base conversion: 1980 base → 2003 base
scale_1980_to_2003 <- 100 / as.numeric(Pk_1980)

## ---------------------------------------------------------
## 6. Rebase Kg and Kn to constant 2003 CLP (same unit as Hofman, typically millions)
## ---------------------------------------------------------
Kg_1950_2003 <- Kg_1950_1980 %>%
  mutate(across(-year, ~ .x * scale_1980_to_2003))

Kn_1950_2003 <- Kn_1950_1980 %>%
  mutate(across(-year, ~ .x * scale_1980_to_2003))

## ---------------------------------------------------------
## 7. Assemble anchor table (two rows: 1980-base and 2003-base)
## ---------------------------------------------------------
make_anchor_row <- function(prices_value, pk_index_value, Kg_row, Kn_row, unit_label) {
  tibble(
    year      = Kg_row$year,
    prices    = prices_value,
    pk_index  = pk_index_value,
    unit      = unit_label,
    Kg_ME     = Kg_row$ME,
    Kg_C      = Kg_row$C,
    Kg_NRC    = Kg_row$NRC,
    Kg_RC     = Kg_row$RC,
    Kg_T      = Kg_row$T,
    Kg_NR     = Kg_row$NR,
    Kn_ME     = Kn_row$ME,
    Kn_C      = Kn_row$C,
    Kn_NRC    = Kn_row$NRC,
    Kn_RC     = Kn_row$RC,
    Kn_T      = Kn_row$T,
    Kn_NR     = Kn_row$NR
  )
}

anchor_1950 <- bind_rows(
  make_anchor_row(
    prices_value   = 1980,
    pk_index_value = as.numeric(Pk_1980),
    Kg_row         = Kg_1950_1980,
    Kn_row         = Kn_1950_1980,
    unit_label     = HOFMAN_UNIT_LABEL
  ),
  make_anchor_row(
    prices_value   = 2003,
    pk_index_value = as.numeric(Pk_2003),
    Kg_row         = Kg_1950_2003,
    Kn_row         = Kn_1950_2003,
    unit_label     = paste0("Rebased_2003_CLP_using_Pk1980 (", HOFMAN_UNIT_LABEL, ")")
  )
) %>% arrange(prices)

## ---------------------------------------------------------
## 8. Integrity checks (additivity + Kn ≤ Kg)
## ---------------------------------------------------------
check_additivity_anchor <- function(df) {
  out <- df %>%
    transmute(
      year, prices,
      res_Kg_C  = Kg_C  - (Kg_NRC  + Kg_RC),
      res_Kg_NR = Kg_NR - (Kg_ME   + Kg_NRC),
      res_Kg_T  = Kg_T  - (Kg_ME   + Kg_NRC + Kg_RC),
      res_Kn_C  = Kn_C  - (Kn_NRC  + Kn_RC),
      res_Kn_NR = Kn_NR - (Kn_ME   + Kn_NRC),
      res_Kn_T  = Kn_T  - (Kn_ME   + Kn_NRC + Kn_RC)
    )
  
  max_res <- max(abs(unlist(out[ , -(1:2)])), na.rm = TRUE)
  message("Additivity check — max |residual| = ",
          format(max_res, scientific = TRUE))
  invisible(out)
}

check_kn_le_kg <- function(df) {
  viol <- df %>%
    mutate(
      v_ME  = Kn_ME  > Kg_ME,
      v_NRC = Kn_NRC > Kg_NRC,
      v_RC  = Kn_RC  > Kg_RC,
      v_C   = Kn_C   > Kg_C,
      v_NR  = Kn_NR  > Kg_NR,
      v_T   = Kn_T   > Kg_T
    ) %>%
    filter(if_any(starts_with("v_"), ~ .x))
  
  if (nrow(viol) > 0) {
    warning("Kn > Kg violations detected in anchor_1950:\n",
            paste(capture.output(print(viol)), collapse = "\n"))
  } else {
    message("Kn ≤ Kg check — OK (no violations).")
  }
}

check_additivity_anchor(anchor_1950)
check_kn_le_kg(anchor_1950)

## ---------------------------------------------------------
## 9. Export
## ---------------------------------------------------------
saveRDS(anchor_1950, file.path(dir_data_interim, "anchor_1950.rds"))
message("anchor_1950.rds successfully saved to: ", file.path(dir_data_interim, "anchor_1950.rds"))

## Optional: print the two anchor rows
print(anchor_1950)
