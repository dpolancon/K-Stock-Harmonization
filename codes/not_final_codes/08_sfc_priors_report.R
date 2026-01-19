############################################################
## 08_sfc_priors_report.R
## Reporte de priors y outliers SFC (sin reconstruir nada)
############################################################

library(dplyr)
library(tidyr)
library(stringr)
library(purrr)
library(here)

dir_int <- here("data","interim")

## ---------------------------------------------------------
## 1. Cargar priors y panel SFC
## ---------------------------------------------------------
sfc_priors <- readRDS(file.path(dir_int, "sfc_priors_2003.rds"))
panel      <- readRDS(file.path(dir_int, "panel_sfc_2003.rds"))

priors_delta <- sfc_priors$priors_delta
priors_z     <- sfc_priors$priors_z
priors_q     <- sfc_priors$priors_q
outliers     <- sfc_priors$outliers

cat("\n========================================\n")
cat("REPORTE PRIORS SFC – δ, z, Kg/Kn\n")
cat("========================================\n\n")

## Helper de redondeo para imprimir bonito
round_df <- function(df, digits = 2) {
  df %>% mutate(across(where(is.numeric), ~ round(.x, digits)))
}

## ---------------------------------------------------------
## 2. Priors δ por activo (ventana 1950–1994)
## ---------------------------------------------------------
cat(">>> Priors δ_t (ventana 1950–1994):\n")
print(
  priors_delta %>%
    select(asset, min, p10, p25, median, mean, p75, p90, max,
           plausible_low, plausible_high) %>%
    round_df(2)
)
cat("\n")

## ---------------------------------------------------------
## 3. Priors z por activo (ventana 1950–1994)
## ---------------------------------------------------------
cat(">>> Priors z_t (ventana 1950–1994):\n")
print(
  priors_z %>%
    select(asset, min, p10, p25, median, mean, p75, p90, max,
           plausible_low, plausible_high) %>%
    round_df(2)
)
cat("\n")

## ---------------------------------------------------------
## 4. Priors razón q = Kg/Kn por activo
## ---------------------------------------------------------
cat(">>> Priors razón q = Kg/Kn (todo el período disponible):\n")
print(
  priors_q %>%
    select(asset, min_q, p25_q, median_q, mean_q, p75_q, max_q,
           plausible_low_q, plausible_high_q) %>%
    round_df(3)
)
cat("\n")

## ---------------------------------------------------------
## 5. Outliers δ y z por activo y período histórico
## ---------------------------------------------------------
cat(">>> Outliers por activo y período histórico:\n")

outliers_with_period <- outliers %>%
  left_join(panel %>% select(year, asset, period) %>% distinct(),
            by = c("year","asset"))

outlier_summary <- outliers_with_period %>%
  group_by(asset, period) %>%
  summarise(
    n_delta_out = sum(delta_outlier, na.rm = TRUE),
    n_z_out     = sum(z_outlier,     na.rm = TRUE),
    .groups     = "drop"
  )

print(outlier_summary)
cat("\n")

## ---------------------------------------------------------
## 6. Años “problemáticos” por activo (top 10)
## ---------------------------------------------------------
cat(">>> Años con outliers (δ o z) por activo – primeros 10 años listados:\n")

years_problem <- outliers_with_period %>%
  filter(delta_outlier | z_outlier) %>%
  group_by(asset, year) %>%
  summarise(
    any_delta = any(delta_outlier, na.rm = TRUE),
    any_z     = any(z_outlier,     na.rm = TRUE),
    .groups   = "drop"
  ) %>%
  arrange(asset, year)

# Imprimir un resumen compacto
years_problem %>%
  group_split(asset) %>%
  purrr::walk(function(df_asset){
    a <- unique(df_asset$asset)
    cat("\nActivo:", a, "\n")
    print(head(df_asset, 10))  # muestra sólo los primeros 10 por activo
  })

cat("\n\n========================================\n")
cat(" FIN REPORTE PRIORS SFC\n")
cat("========================================\n\n")
