############################################################
## 06_sfc_engine.R  —  TD–SFC COMPLIANT VERSION
## Stock–flow consistent capital stock reconstruction (Chile)
##
## Objetivos:
##  - Integrar Ig, Kg, Kn en 2003 CLP en un único panel
##  - Calcular dKg, dKn, D, R, δ, z con denominadores rezagados
##  - Calcular i_t, FNKF_t, Kn/Kg y residuales de acumulación
##  - Definir ventanas históricas de trabajo
##  - Exportar panel_sfc_2003.rds
##
## Nota:
##  - D y R aquí son magnitudes implícitas, derivadas de Ig, Kg, Kn.
##  - La armonización / evaluación (FLOW/STOCK/RATE/SPLICE) se hace
##    aguas arriba con /harmonize_cluster1_SFC y scripts 07–09.
############################################################

## -------------------------
## 0. Librerías & setup
## -------------------------
library(dplyr)
library(tidyr)
library(stringr)
library(here)

source(here("codes","00_setup.R"))    # rutas y helpers (dir_data_interim, check_additivity, etc.)

## -------------------------
## 1. Cargar insumos
## -------------------------
Ig_2003 <- readRDS(file.path(dir_data_interim, "Ig_2003.rds"))
Kg_2003 <- readRDS(file.path(dir_data_interim, "Kg_2003.rds"))
Kn_2003 <- readRDS(file.path(dir_data_interim, "Kn_2003.rds"))

## Verificación mínima de estructura
req_cols <- c("year","asset","var","value")
stopifnot(all(req_cols %in% names(Ig_2003)))
stopifnot(all(req_cols %in% names(Kg_2003)))
stopifnot(all(req_cols %in% names(Kn_2003)))

## -------------------------
## 2. Integrar panel largo → ancho
## -------------------------
panel_long <- bind_rows(
  Ig_2003 %>% select(year, asset, var, value),
  Kg_2003 %>% select(year, asset, var, value),
  Kn_2003 %>% select(year, asset, var, value)
)

panel_wide <- panel_long %>%
  distinct(year, asset, var, value) %>%      # evita duplicados si los hubiera
  tidyr::pivot_wider(names_from = var, values_from = value) %>%
  arrange(asset, year)

## Esperamos columnas: Ig, Kg, Kn
if (!all(c("Ig","Kg","Kn") %in% names(panel_wide))) {
  stop("panel_wide no contiene las columnas Ig, Kg y Kn. Revisar scripts 03–05.")
}

## -------------------------
## 3. Safe division helper
## -------------------------
safe_div <- function(num, denom, tol = 0) {
  if_else(!is.na(denom) & abs(denom) > tol, num / denom, NA_real_)
}

## -------------------------
## 4. Calcular magnitudes SFC
##    (todo implícito a partir de Ig, Kg, Kn)
## -------------------------
panel_sfc <- panel_wide %>%
  group_by(asset) %>%
  arrange(year, .by_group = TRUE) %>%
  mutate(
    ## Capital rezagado
    Kg_lag = dplyr::lag(Kg),
    Kn_lag = dplyr::lag(Kn),
    
    ## Variaciones de existencias
    dKg = Kg - Kg_lag,
    dKn = Kn - Kn_lag,
    
    ## Depreciación y retiros implícitos (stock-flow identities)
    D = Ig - dKn,   # desde Kn_t - Kn_{t-1} = Ig_t - D_t
    R = Ig - dKg,   # desde Kg_t - Kg_{t-1} = Ig_t - R_t
    
    ## Tasas implícitas (DENOMINADORES REZAGADOS)
    delta = safe_div(D, Kn_lag),   # δ_t = D_t / Kn_{t-1}
    z     = safe_div(R, Kg_lag),   # z_t = R_t / Kg_{t-1}
    
    ## Ratio inversión-capital (real)
    i = safe_div(Ig, Kg_lag),      # i_t = Ig_t / Kg_{t-1}
    
    ## Formación neta de capital fijo
    FNKF = Ig - D,
    
    ## Ordenamiento neto–bruto (para red flags)
    Kn_over_Kg = safe_div(Kn, Kg),
    
    ## Residuos de acumulación (deberían ser ~0 con definiciones implícitas)
    eps_Kg = dKg - (Ig - R),       # Kg_t - Kg_{t-1} ?= Ig_t - R_t
    eps_Kn = dKn - (Ig - D),       # Kn_t - Kn_{t-1} ?= Ig_t - D_t
    
    ## Residuo combinado (teóricamente redundante, pero útil sanity check)
    eps_joint = (D - R) - (dKg - dKn),
    
    ## Flag mínimo: violación orden neto/bruto
    flag_Kn_gt_Kg = !is.na(Kn) & !is.na(Kg) & (Kn > Kg)
  ) %>%
  ungroup()

## -------------------------
## 5. Ventanas históricas y flags de análisis
## -------------------------
panel_sfc <- panel_sfc %>%
  mutate(
    period = dplyr::case_when(
      year <= 1949 ~ "1900_1949",
      year <= 1994 ~ "1950_1994",
      TRUE         ~ "1995_plus"
    ),
    
    ## Ventana donde Clio + Hofman están plenamente alineados
    full_SFC_window = year >= 1950 & year <= 1994,
    
    ## Ventana extendida típica para ME (según disponibilidad TD/Clio)
    full_ME_window  = asset == "ME" & year >= 1900 & year <= 2008
  )

## -------------------------
## 6. Guardar resultado
## -------------------------
saveRDS(panel_sfc, file.path(dir_data_interim, "panel_sfc_2003.rds"))

message(">>> 06_sfc_engine.R COMPLETADO: panel_sfc_2003.rds guardado con éxito.")

############################################################
## Fin de 06_sfc_engine.R
############################################################
