############################################################
## 03_build_Ig_2003.R — TD–SFC COMPLIANT VERSION
## Stock–flow consistent capital stock reconstruction (Chile)
##
## Objetivo:
##  - Construir Ig en 2003 CLP por activo (ME, NRC, RC, C, NR, T)
##  - Usar como insumo canónico Ig_2003_pattern.rds
##    (Pérez–Eyzaguirre = nivel; Hofman + Tafunell = patrón)
##  - Verificar identidades de aditividad vía check_additivity()
############################################################

## -------------------------
## 0. Librerías y setup
## -------------------------
library(dplyr)
library(tidyr)
library(here)
library(rlang)

source(here("codes", "00_setup.R"))  # dirs, check_additivity(), etc.


## -------------------------
## 1. Cargar insumos intermedios
## -------------------------
Ig_2003_pattern <- readRDS(
  file.path(dir_data_interim, "Ig_2003_pattern.rds")
)

# Sanity check mínimo
if (!all(c("year", "asset", "value") %in% names(Ig_2003_pattern))) {
  stop("Ig_2003_pattern.rds no tiene las columnas esperadas: year, asset, value.")
}

## -------------------------
## 2. Limpiar y fijar activos base
##    Usamos ME, NRC y RC como bloques “primitivos”
##    y construimos C, NR y T como identidades.
## -------------------------

# Nos quedamos solo con las filas relevantes
Ig_base <- Ig_2003_pattern %>%
  filter(asset %in% c("ME", "NRC", "RC")) %>%
  select(year, asset, value)

# Chequeo: que no falte ningún asset clave por año
missing_assets <- Ig_base %>%
  group_by(year) %>%
  reframe(miss_assets = list(setdiff(c("ME","NRC","RC"), asset))) %>%
  ungroup() %>%
  filter(lengths(miss_assets) > 0)

if (nrow(missing_assets) > 0) {
  warning("Hay años con activos ME/NRC/RC faltantes en Ig_2003_pattern. Revisa Ig_2003_pattern.rds.")
}


## -------------------------
## 3. Construir panel ancho con ME, NRC, RC
## -------------------------
Ig_wide <- Ig_base %>%
  tidyr::pivot_wider(
    names_from  = asset,
    values_from = value
  )

## -------------------------
## 4. Construir agregados C, NR, T por identidades
## -------------------------
Ig_decomp <- Ig_wide %>%
  mutate(
    Ig_ME_2003  = ME,
    Ig_NRC_2003 = NRC,
    Ig_RC_2003  = RC,
    Ig_C_2003   = Ig_NRC_2003 + Ig_RC_2003,
    Ig_NR_2003  = Ig_ME_2003  + Ig_NRC_2003,
    Ig_T_2003   = Ig_ME_2003  + Ig_C_2003
  ) %>%
  select(
    year,
    ME  = Ig_ME_2003,
    NRC = Ig_NRC_2003,
    RC  = Ig_RC_2003,
    C   = Ig_C_2003,
    NR  = Ig_NR_2003,
    T   = Ig_T_2003
  )

## -------------------------
## 5. Panel largo final Ig_2003
## -------------------------
Ig_2003 <- Ig_decomp %>%
  tidyr::pivot_longer(
    cols      = -year,
    names_to  = "asset",
    values_to = "value"
  ) %>%
  mutate(
    var        = "Ig",
    price_base = "2003_CLP",
    source     = "AD (niveles) + Hofman & Tafunell (patrones)"
  ) %>%
  arrange(year, asset)

saveRDS(Ig_2003, file.path(dir_data_interim, "Ig_2003.rds"))

## -------------------------
## 6. Chequeo de aditividad para Ig
## -------------------------
Ig_2003_additivity <- check_additivity(Ig_2003, "Ig")
saveRDS(Ig_2003_additivity, file.path(dir_data_interim, "Ig_2003_additivity.rds"))
message(">>> 03_build_Ig_2003.R completado: Ig_2003 y residuos de aditividad guardados.")

############################################################
## Fin de 03_build_Ig_2003.R
############################################################
