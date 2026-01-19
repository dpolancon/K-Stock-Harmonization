############################################################
## 04_build_Kg_2003.R — TD–SFC COMPLIANT (Opción 1)
## Reconstrucción SFC del stock bruto de capital (Kg, 2003 CLP)
##
## Lógica:
##  - Patrón temporal: Tafunell–Ducoing 2016 (Kg_index) para ME y NRC
##  - Niveles absolutos (1950, 2003 CLP): anchor_1950.rds (Hofman 2000)
##  - RC_t = RC_1950 * (NRC_t / NRC_1950)   [Opción 1]
##  - Agregados: NR, C, T por identidades:
##       NR = ME + NRC
##       C  = NRC + RC
##       T  = ME + NRC + RC
##  - Output: Kg_2003.rds + Kg_2003_additivity_residuals.rds
############################################################

library(dplyr)
library(tidyr)
library(here)

source(here("codes","00_setup.R"))   # dirs, check_additivity(), etc.

############################################################
## 1. CARGAR INSUMOS
############################################################

td_Kg       <- readRDS(file.path(dir_data_interim, "raw_TD_indices.rds"))
anchor_1950 <- readRDS(file.path(dir_data_interim, "anchor_1950.rds"))
raw_AD      <- readRDS(file.path(dir_data_interim, "raw_AD.rds"))

# Ventana de años objetivo (alineada con AD)
years_AD <- raw_AD %>%
  dplyr::pull(year) %>%
  unique() %>%
  sort()

############################################################
## 2. EXTRAER ANCLAS 1950 EN PRECIOS 2003 (ME, NRC, RC)
############################################################

anchor_Kg_1950 <- anchor_1950 %>%
  dplyr::filter(prices == 2003, year == 1950) %>%
  dplyr::select(
    year,
    Kg_ME, Kg_NRC, Kg_RC
  ) %>%
  tidyr::pivot_longer(
    cols      = starts_with("Kg_"),
    names_to  = "asset_raw",
    values_to = "Kg_2003_anchor"
  ) %>%
  dplyr::mutate(asset = sub("^Kg_", "", asset_raw)) %>%
  dplyr::select(asset, Kg_2003_anchor)

# Chequeos básicos
needed_assets <- c("ME","NRC","RC")
if (!all(needed_assets %in% anchor_Kg_1950$asset)) {
  stop("Faltan Kg_2003_anchor para alguno de: ME, NRC, RC en anchor_1950.rds.")
}

anchor_ME_1950  <- anchor_Kg_1950 %>% dplyr::filter(asset == "ME")  %>% dplyr::pull(Kg_2003_anchor)
anchor_NRC_1950 <- anchor_Kg_1950 %>% dplyr::filter(asset == "NRC") %>% dplyr::pull(Kg_2003_anchor)
anchor_RC_1950  <- anchor_Kg_1950 %>% dplyr::filter(asset == "RC")  %>% dplyr::pull(Kg_2003_anchor)

############################################################
## 3. CAMINOS TD-2016 PARA ME Y NRC
############################################################

kg_td_assets <- c("ME","NRC")

td_prim <- td_Kg %>%
  dplyr::filter(
    var   == "Kg_index",
    asset %in% kg_td_assets
  )

# Años con índice TD
years_TD <- sort(unique(td_prim$year))

# Intersección con AD: sólo donde ambas fuentes existen
years_use <- intersect(years_AD, years_TD)

if (length(years_use) == 0) {
  stop("No hay intersección de años entre AD y TD-2016 para construir Kg.")
}

td_prim <- td_prim %>%
  dplyr::filter(year %in% years_use)

# Índice equivalente a 1950 por activo (interpolación/extrapolación lineal)
td_1950 <- td_prim %>%
  dplyr::group_by(asset) %>%
  dplyr::summarise(
    idx_1950 = approx(
      x    = year,
      y    = value,
      xout = 1950,
      rule = 2   # extrapola fuera de rango si hace falta
    )$y,
    .groups = "drop"
  )

if (any(is.na(td_1950$idx_1950))) {
  warning("Algún activo tiene idx_1950 NA tras interpolación; revisar raw_TD_indices.rds.")
}

############################################################
## 4. CONSTRUIR Kg_2003 PARA ME Y NRC (TD + ancla 1950)
############################################################

anchor_Kg_1950_MENRC <- anchor_Kg_1950 %>%
  dplyr::filter(asset %in% kg_td_assets)

Kg_ME_NRC <- td_prim %>%
  dplyr::left_join(td_1950,              by = "asset") %>%
  dplyr::left_join(anchor_Kg_1950_MENRC, by = "asset") %>%
  dplyr::mutate(
    Kg_2003 = Kg_2003_anchor * (value / idx_1950)
  ) %>%
  dplyr::transmute(
    year,
    asset,
    value      = Kg_2003,
    var        = "Kg",
    price_base = "2003_CLP",
    source     = "TD_2016_index + Hofman_1950_anchor"
  )

############################################################
## 5. CONSTRUIR RC_t PROPORCIONAL A NRC_t (OPCIÓN 1)
############################################################

# NRC_t ya está en Kg_ME_NRC; usamos su trayectoria para escalar RC.
# Fórmula: RC_t = RC_1950 * (NRC_t / NRC_1950)

Kg_RC <- Kg_ME_NRC %>%
  dplyr::filter(asset == "NRC") %>%
  dplyr::mutate(
    asset      = "RC",
    value      = anchor_RC_1950 * (value / anchor_NRC_1950),
    var        = "Kg",
    price_base = "2003_CLP",
    source     = "RC_scaled_from_NRC_TD + Hofman_1950_anchor"
  )

############################################################
## 6. AGREGAR TODOS LOS ACTIVOS PRIMITIVOS (ME, NRC, RC)
############################################################

Kg_prim_all <- dplyr::bind_rows(
  Kg_ME_NRC,
  Kg_RC
)

############################################################
## 7. CONSTRUIR AGREGADOS NR, C, T POR IDENTIDADES
############################################################

Kg_wide <- Kg_prim_all %>%
  dplyr::select(year, asset, value) %>%
  tidyr::pivot_wider(
    names_from  = asset,
    values_from = value
  )

Kg_wide <- Kg_wide %>%
  dplyr::mutate(
    NR = ME + NRC,
    C  = NRC + RC,
    T  = ME + NRC + RC
  )

Kg_all <- Kg_wide %>%
  tidyr::pivot_longer(
    cols      = c("ME","NRC","RC","C","NR","T"),
    names_to  = "asset",
    values_to = "value"
  ) %>%
  dplyr::mutate(
    var        = "Kg",
    price_base = "2003_CLP",
    source     = dplyr::case_when(
      asset %in% c("ME","NRC") ~ "TD_2016_index + Hofman_1950_anchor",
      asset == "RC"            ~ "RC_scaled_from_NRC_TD + Hofman_1950_anchor",
      TRUE                     ~ "Implied_by_identities_from_primitive_assets"
    )
  ) %>%
  dplyr::arrange(year, asset)

############################################################
## 8. GUARDAR Kg_2003 Y CHEQUEAR ADITIVIDAD
############################################################

Kg_2003 <- Kg_all
saveRDS(Kg_2003, file.path(dir_data_interim, "Kg_2003.rds"))

Kg_2003_add <- check_additivity(Kg_2003, "Kg")
saveRDS(Kg_2003_add, file.path(dir_data_interim, "Kg_2003_additivity_residuals.rds"))

message(">>> 04_build_Kg_2003.R completado: Kg_2003 y residuos de aditividad guardados (Opción 1: RC ∝ NRC).")
############################################################
## FIN DE 04_build_Kg_2003.R
############################################################
