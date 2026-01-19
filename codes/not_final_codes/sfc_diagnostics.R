############################################################
## 06_sfc_diagnostics.R
## Diagnósticos SFC sobre panel_sfc_2003
##
## Objetivos:
##  - Resumir cobertura de delta, z y eps_joint
##  - Detectar outliers fuertes en delta y z por activo
##  - Revisar residuo SFC (eps_joint, r_joint_*)
##  - Proveer función plot_sfc_diagnostics(asset)
############################################################

## -------------------------
## 0. Librerías & setup
## -------------------------
library(dplyr)
library(tidyr)
library(stringr)
library(purrr)
library(ggplot2)
library(here)

## Si necesitas helpers de 00_setup, descomenta:
## source(here("codes","00_setup.R"))

dir_int <- here("data","interim")

## -------------------------
## 1. Cargar insumos
## -------------------------
panel_sfc <- readRDS(file.path(dir_int, "panel_sfc_2003.rds"))

Ig_2003 <- readRDS(file.path(dir_int, "Ig_2003.rds"))
Kg_2003 <- readRDS(file.path(dir_int, "Kg_2003.rds"))
Kn_2003 <- readRDS(file.path(dir_int, "Kn_2003.rds"))

## Verificación mínima
stopifnot(all(c("year","asset","Ig","Kg","Kn") %in% names(panel_sfc)))
stopifnot(all(c("delta","z","eps_joint",
                "r_joint_Ig","r_joint_Kg","r_joint_Kn") %in% names(panel_sfc)))

cat("\n========================================\n")
cat("06_sfc_diagnostics.R – Carga completada\n")
cat("========================================\n\n")

## -------------------------
## 2. Cobertura de delta, z, eps_joint
## -------------------------
cov_sfc <- panel_sfc %>%
  group_by(asset) %>%
  summarise(
    min_year   = min(year),
    max_year   = max(year),
    n          = n(),
    n_delta    = sum(!is.na(delta)),
    n_z        = sum(!is.na(z)),
    n_eps      = sum(!is.na(eps_joint)),
    share_delta = n_delta / n,
    share_z     = n_z     / n,
    share_eps   = n_eps   / n,
    .groups = "drop"
  )

cat(">>> Cobertura de delta, z y eps_joint por activo:\n")
print(cov_sfc)
cat("\n\n")

## -------------------------
## 3. Helper outliers (IQR rule)
## -------------------------
## Devuelve tabla de outliers para una variable continua
detect_outliers_var <- function(df, var, by_asset = TRUE, k_iqr = 3) {
  v <- rlang::ensym(var)
  
  base <- df %>%
    filter(!is.na(!!v))
  
  if (by_asset) {
    base <- base %>% group_by(asset)
  } else {
    base <- base %>% mutate(asset = "ALL") %>% group_by(asset)
  }
  
  base %>%
    summarise(
      q25 = quantile(!!v, 0.25, na.rm = TRUE),
      q75 = quantile(!!v, 0.75, na.rm = TRUE),
      iqr = q75 - q25,
      .groups = "drop"
    ) %>%
    left_join(
      base,
      by = dplyr::group_vars(base)
    ) %>%
    mutate(
      upper = q75 + k_iqr * iqr,
      lower = q25 - k_iqr * iqr,
      is_outlier = (!!v > upper) | (!!v < lower)
    ) %>%
    filter(is_outlier) %>%
    arrange(asset, year)
}

## -------------------------
## 4. Outliers en delta y z por activo
## -------------------------
delta_out <- detect_outliers_var(panel_sfc, delta, by_asset = TRUE, k_iqr = 3) %>%
  select(asset, year, delta, period, full_SFC_window, dKg, dKn, Ig, Kg, Kn)

z_out <- detect_outliers_var(panel_sfc, z, by_asset = TRUE, k_iqr = 3) %>%
  select(asset, year, z, period, full_SFC_window, dKg, dKn, Ig, Kg, Kn)

cat(">>> Outliers (IQR*3) en delta por activo:\n")
print(delta_out)
cat("\n\n")

cat(">>> Outliers (IQR*3) en z por activo:\n")
print(z_out)
cat("\n\n")

## Si quieres guardar en RDS:
saveRDS(delta_out, file.path(dir_int, "delta_outliers_IQR3.rds"))
saveRDS(z_out,     file.path(dir_int, "z_outliers_IQR3.rds"))

## -------------------------
## 5. Resumen de eps_joint y residuales normalizados
## -------------------------
eps_summary <- panel_sfc %>%
  group_by(asset, period) %>%
  summarise(
    n          = n(),
    n_eps      = sum(!is.na(eps_joint)),
    mean_eps   = mean(eps_joint, na.rm = TRUE),
    sd_eps     = sd(eps_joint, na.rm = TRUE),
    mean_r_Ig  = mean(r_joint_Ig, na.rm = TRUE),
    mean_r_Kg  = mean(r_joint_Kg, na.rm = TRUE),
    mean_r_Kn  = mean(r_joint_Kn, na.rm = TRUE),
    max_abs_r_Kg = max(abs(r_joint_Kg), na.rm = TRUE),
    .groups = "drop"
  )

cat(">>> Resumen eps_joint y r_joint_* por activo y período:\n")
print(eps_summary)
cat("\n\n")

saveRDS(eps_summary, file.path(dir_int, "eps_summary_by_asset_period.rds"))

## -------------------------
## 6. Función de gráficos: plot_sfc_diagnostics(asset)
## -------------------------
plot_sfc_diagnostics <- function(target_asset = "ME") {
  
  df <- panel_sfc %>%
    filter(asset == target_asset)
  
  if (nrow(df) == 0) {
    stop(paste("Activo", target_asset, "no encontrado en panel_sfc."))
  }
  
  ## Sombras para ventana SFC 1950–1994
  sfc_start <- 1950
  sfc_end   <- 1994
  
  ## 6.1 Ig, Kg, Kn (escala log opcional)
  p_levels <- ggplot(df, aes(x = year)) +
    geom_line(aes(y = Ig, colour = "Ig")) +
    geom_line(aes(y = Kg, colour = "Kg")) +
    geom_line(aes(y = Kn, colour = "Kn")) +
    annotate("rect",
             xmin = sfc_start, xmax = sfc_end,
             ymin = -Inf, ymax = Inf,
             alpha = 0.1) +
    scale_y_continuous(labels = scales::comma) +
    labs(
      title = paste("Niveles Ig, Kg, Kn –", target_asset),
      y = "2003 CLP (niveles)",
      x = "Año",
      colour = "Serie"
    ) +
    theme_minimal()
  
  ## 6.2 delta_t
  p_delta <- ggplot(df, aes(x = year, y = delta)) +
    geom_hline(yintercept = 0, linetype = "dashed") +
    geom_line() +
    annotate("rect",
             xmin = sfc_start, xmax = sfc_end,
             ymin = -Inf, ymax = Inf,
             alpha = 0.1) +
    labs(
      title = bquote(delta[t] ~ " implícita – " ~ .(target_asset)),
      y = expression(delta[t]),
      x = "Año"
    ) +
    theme_minimal()
  
  ## 6.3 z_t
  p_z <- ggplot(df, aes(x = year, y = z)) +
    geom_hline(yintercept = 0, linetype = "dashed") +
    geom_line() +
    annotate("rect",
             xmin = sfc_start, xmax = sfc_end,
             ymin = -Inf, ymax = Inf,
             alpha = 0.1) +
    labs(
      title = bquote(z[t] ~ " implícita – " ~ .(target_asset)),
      y = expression(z[t]),
      x = "Año"
    ) +
    theme_minimal()
  
  ## 6.4 residuo SFC normalizado por Kg
  p_rKg <- ggplot(df, aes(x = year, y = r_joint_Kg)) +
    geom_hline(yintercept = 0, linetype = "dashed") +
    geom_line() +
    annotate("rect",
             xmin = sfc_start, xmax = sfc_end,
             ymin = -Inf, ymax = Inf,
             alpha = 0.1) +
    labs(
      title = bquote("Residuo SFC normalizado (eps_joint / Kg) – " ~ .(target_asset)),
      y = expression(r[joint]^Kg),
      x = "Año"
    ) +
    theme_minimal()
  
  ## Imprimir secuencialmente
  print(p_levels)
  print(p_delta)
  print(p_z)
  print(p_rKg)
  
  invisible(list(
    levels = p_levels,
    delta  = p_delta,
    z      = p_z,
    rKg    = p_rKg
  ))
}

cat(">>> 06_sfc_diagnostics.R listo.\n")
cat("    Usa plot_sfc_diagnostics('ME') (o 'NR','C', etc.) para ver gráficos.\n\n")


plot_sfc_diagnostics("ME")
plot_sfc_diagnostics("NR")
plot_sfc_diagnostics("NRC")
plot_sfc_diagnostics("RC")
plot_sfc_diagnostics("C")
