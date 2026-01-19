############################################################
## 07_sfc_priors.R
## Priors estructurales para reconstrucción SFC de capital
## Proyecto: Reconstrucción Stock–Flow Consistent (Chile)
##
## Objetivos:
##   - Cargar panel_sfc_2003 (δ, z, Kg/Kn)
##   - Calcular priors robustos por activo (1950–1994)
##   - Identificar rangos plausibles de δ y z
##   - Caracterizar razón Kg/Kn e identificar outliers
##   - Guardar priors para uso en 08_sfc_reconstruct.R
############################################################

library(dplyr)
library(tidyr)
library(stringr)
library(purrr)
library(here)

source(here("codes","00_setup.R"))   # rutas + helpers

dir_int <- here("data","interim")

############################################################
## 1. Cargar panel SFC
############################################################

panel <- readRDS(file.path(dir_int, "panel_sfc_2003.rds"))

stopifnot(all(c("Kg","Kn","Ig","delta","z","period") %in% names(panel)))

cat("\n==========================================\n")
cat(" 07_sfc_priors.R – Carga de panel OK\n")
cat("==========================================\n\n")


############################################################
## 2. Definir ventana de alta calidad (1950–1994)
############################################################

panel_HQ <- panel %>% filter(full_SFC_window)

if(nrow(panel_HQ) == 0){
  stop("No existen datos para la ventana 1950–1994; revisar panel_sfc.")
}

assets <- sort(unique(panel$asset))


############################################################
## 3. Función para estadísticos robustos
############################################################

stats_prior <- function(x){
  tibble(
    min      = min(x, na.rm=TRUE),
    p10      = quantile(x, 0.10, na.rm=TRUE),
    p25      = quantile(x, 0.25, na.rm=TRUE),
    median   = median(x, na.rm=TRUE),
    mean     = mean(x, na.rm=TRUE),
    p75      = quantile(x, 0.75, na.rm=TRUE),
    p90      = quantile(x, 0.90, na.rm=TRUE),
    max      = max(x, na.rm=TRUE),
    sd       = sd(x, na.rm=TRUE),
    iqr      = IQR(x, na.rm=TRUE)
  )
}


############################################################
## 4. Priors δ_t y z_t por activo (1950–1994)
############################################################

priors_delta <- panel_HQ %>%
  group_by(asset) %>%
  summarise(stats_prior(delta), .groups="drop") %>%
  mutate(
    plausible_low  = p10,
    plausible_high = p90
  )

priors_z <- panel_HQ %>%
  group_by(asset) %>%
  summarise(stats_prior(z), .groups="drop") %>%
  mutate(
    plausible_low  = p10,
    plausible_high = p90
  )

cat(">>> Priors para δ y z generados correctamente.\n\n")


############################################################
## 5. Razón Kg/Kn por activo
############################################################

panel <- panel %>%
  mutate(q = Kg / Kn)

priors_q <- panel %>%
  filter(!is.na(q), is.finite(q)) %>%
  group_by(asset) %>%
  summarise(
    min_q = min(q),
    p25_q = quantile(q, 0.25),
    median_q = median(q),
    mean_q = mean(q),
    p75_q = quantile(q, 0.75),
    max_q = max(q),
    sd_q   = sd(q),
    iqr_q  = IQR(q),
    .groups = "drop"
  ) %>%
  mutate(
    plausible_low_q  = p25_q - 1.5 * iqr_q,
    plausible_high_q = p75_q + 1.5 * iqr_q
  )

cat(">>> Priors para la razón Kg/Kn generados.\n\n")


############################################################
## 6. Identificación de outliers δ y z
############################################################

panel_outliers <- panel %>%
  left_join(priors_delta %>% select(asset, delta_low=plausible_low, delta_high=plausible_high),
            by="asset") %>%
  left_join(priors_z %>% select(asset, z_low=plausible_low, z_high=plausible_high),
            by="asset") %>%
  mutate(
    delta_outlier = delta < delta_low | delta > delta_high,
    z_outlier     = z     < z_low     | z     > z_high
  ) %>%
  select(year, asset, delta, z, delta_outlier, z_outlier)

n_out_delta <- sum(panel_outliers$delta_outlier, na.rm=TRUE)
n_out_z     <- sum(panel_outliers$z_outlier, na.rm=TRUE)

cat(">>> Outliers detectados:\n")
cat("    δ outliers:", n_out_delta, "\n")
cat("    z outliers:", n_out_z, "\n\n")


############################################################
## 7. Armar lista final de priors
############################################################

sfc_priors <- list(
  priors_delta = priors_delta,
  priors_z     = priors_z,
  priors_q     = priors_q,
  outliers     = panel_outliers
)

saveRDS(sfc_priors, file.path(dir_int, "sfc_priors_2003.rds"))

cat("==========================================\n")
cat(" 07_sfc_priors.R COMPLETADO\n")
cat(" Priors guardados en data/interim/sfc_priors_2003.rds\n")
cat("==========================================\n\n")
