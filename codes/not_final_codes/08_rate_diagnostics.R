############################################################
## 08_rate_diagnostics.R  —  TD–SFC COMPLIANT VERSION
## Objetivo:
##   - Diagnosticar el comportamiento de δ, z, i, FNKF, Kn/Kg
##   - Resumir por activo y período histórico
##   - Identificar outliers “económicamente sospechosos”
##   - Exportar:
##       * rates_summary_by_asset_period.rds
##       * rates_summary_overall.rds
##       * rates_outliers_long.rds
############################################################

library(dplyr)
library(tidyr)
library(purrr)
library(here)

## 00_setup.R debe definir al menos dir_data_interim y/o helpers
source(here("codes", "00_setup.R"))

## -----------------------------------------------------------------
## 1. Cargar panel SFC
## -----------------------------------------------------------------
panel_sfc <- readRDS(file.path(dir_data_interim, "panel_sfc_2003.rds"))

req_cols <- c("year","asset","period","delta","z","i","FNKF","Kn_over_Kg",
              "D","R","Kg","Kn","Ig")
if (!all(req_cols %in% names(panel_sfc))) {
  stop("08_rate_diagnostics: faltan columnas esperadas en panel_sfc_2003.rds.")
}

## -----------------------------------------------------------------
## 2. Parámetros de diagnóstico (ajustables)
## -----------------------------------------------------------------
delta_hi <- 0.20   # δ > 20% anual es sospechoso para stocks agregados
z_hi     <- 0.20   # z > 20% anual de retiros también
i_hi     <- 0.40   # Ig / Kg_{t-1} > 40%: inversión extremadamente alta
eps_tol  <- 1e-8   # tolerancia numérica para residuales (por si se usan)

## -----------------------------------------------------------------
## 3. Función helper: resumen univariado robusto
## -----------------------------------------------------------------
summarise_var <- function(x) {
  x_valid <- x[is.finite(x)]
  if (length(x_valid) == 0) {
    return(
      tibble(
        n_valid = 0L,
        min     = NA_real_,
        q01     = NA_real_,
        q10     = NA_real_,
        median  = NA_real_,
        q90     = NA_real_,
        q99     = NA_real_,
        max     = NA_real_,
        mean    = NA_real_,
        sd      = NA_real_
      )
    )
  }
  tibble(
    n_valid = length(x_valid),
    min     = min(x_valid),
    q01     = quantile(x_valid, 0.01),
    q10     = quantile(x_valid, 0.10),
    median  = median(x_valid),
    q90     = quantile(x_valid, 0.90),
    q99     = quantile(x_valid, 0.99),
    max     = max(x_valid),
    mean    = mean(x_valid),
    sd      = sd(x_valid)
  )
}

## -----------------------------------------------------------------
## 4. Resumen por activo y período
## -----------------------------------------------------------------
rates_summary_by_asset_period <- panel_sfc %>%
  group_by(asset, period) %>%
  summarise(
    n_obs = n(),
    
    ## δ
    summarise_var(delta) %>%
      rename_with(~ paste0("delta_", .), everything()),
    
    ## z
    summarise_var(z) %>%
      rename_with(~ paste0("z_", .), everything()),
    
    ## i (Ig/Kg_{t-1})
    summarise_var(i) %>%
      rename_with(~ paste0("i_", .), everything()),
    
    ## FNKF
    summarise_var(FNKF) %>%
      rename_with(~ paste0("FNKF_", .), everything()),
    
    ## Kn/Kg
    summarise_var(Kn_over_Kg) %>%
      rename_with(~ paste0("KnKg_", .), everything()),
    
    ## Flags de outliers / comportamientos problemáticos
    n_delta_neg   = sum(delta < 0, na.rm = TRUE),
    n_delta_hi    = sum(delta > delta_hi, na.rm = TRUE),
    n_z_neg       = sum(z < 0, na.rm = TRUE),
    n_z_hi        = sum(z > z_hi, na.rm = TRUE),
    n_i_neg       = sum(i < 0, na.rm = TRUE),
    n_i_hi        = sum(i > i_hi, na.rm = TRUE),
    n_FNKF_neg    = sum(FNKF < 0, na.rm = TRUE),
    n_Kn_gt_Kg    = sum(Kn_over_Kg > 1 + 1e-10, na.rm = TRUE),
    
    .groups = "drop"
  )

saveRDS(
  rates_summary_by_asset_period,
  file.path(dir_data_interim, "rates_summary_by_asset_period.rds")
)

## -----------------------------------------------------------------
## 5. Resumen global por activo (toda la ventana)
## -----------------------------------------------------------------
rates_summary_overall <- panel_sfc %>%
  group_by(asset) %>%
  summarise(
    n_obs = n(),
    
    summarise_var(delta) %>%
      rename_with(~ paste0("delta_", .), everything()),
    summarise_var(z) %>%
      rename_with(~ paste0("z_", .), everything()),
    summarise_var(i) %>%
      rename_with(~ paste0("i_", .), everything()),
    summarise_var(FNKF) %>%
      rename_with(~ paste0("FNKF_", .), everything()),
    summarise_var(Kn_over_Kg) %>%
      rename_with(~ paste0("KnKg_", .), everything()),
    
    n_delta_neg   = sum(delta < 0, na.rm = TRUE),
    n_delta_hi    = sum(delta > delta_hi, na.rm = TRUE),
    n_z_neg       = sum(z < 0, na.rm = TRUE),
    n_z_hi        = sum(z > z_hi, na.rm = TRUE),
    n_i_neg       = sum(i < 0, na.rm = TRUE),
    n_i_hi        = sum(i > i_hi, na.rm = TRUE),
    n_FNKF_neg    = sum(FNKF < 0, na.rm = TRUE),
    n_Kn_gt_Kg    = sum(Kn_over_Kg > 1 + 1e-10, na.rm = TRUE),
    
    .groups = "drop"
  )

saveRDS(
  rates_summary_overall,
  file.path(dir_data_interim, "rates_summary_overall.rds")
)

## -----------------------------------------------------------------
## 6. Identificar observaciones outlier (para inspección puntual)
## -----------------------------------------------------------------
rates_outliers_long <- panel_sfc %>%
  filter(
    (!is.na(delta) & (delta < 0 | delta > delta_hi)) |
      (!is.na(z)     & (z     < 0 | z     > z_hi))     |
      (!is.na(i)     & (i     < 0 | i     > i_hi))     |
      (!is.na(FNKF)  & FNKF  < 0)                      |
      (!is.na(Kn_over_Kg) & Kn_over_Kg > 1 + 1e-10)
  ) %>%
  arrange(asset, year) %>%
  select(
    year, asset, period,
    delta, z, i, FNKF,
    Kn_over_Kg,
    D, R, Ig, Kg, Kn
  )

saveRDS(
  rates_outliers_long,
  file.path(dir_data_interim, "rates_outliers_long.rds")
)

message(">>> 08_rate_diagnostics.R COMPLETADO: resúmenes y outliers guardados.")
############################################################
## FIN 08_rate_diagnostics.R
############################################################
