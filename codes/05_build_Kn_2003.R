############################################################
## 05_build_Kn_2003.R  — TD–SFC COMPLIANT VERSION
## Reconstrucción SFC del stock NETO (Kn) en 2003 CLP
##
## Principles:
##  1) Hofman is the only benchmark for levels, 1950–1994.
##  2) Clio-Lab provides ONLY relative profiles pre-1950
##     for ME (machinery) and INF/C (total infrastructure).
##  3) The NRC / RC split comes EXCLUSIVELY
##     from the Hofman shares in 1950.
##
## Strategy:
##  - Pre-1950 (1900–1949):
##      * Kn_ME(t) = Kn_ME_2003(1950) * SK_MAQ(t) / SK_MAQ(1950)
##      * Kn_C(t)  = Kn_C_2003(1950)  * SK_INF(t) / SK_INF(1950)
##      * NRC, RC via Hofman 1950 shares: θ_NRC, θ_RC
##      * NR = ME + NRC; T = ME + NRC + RC
##
##  - 1950–1994:
##      * Kn_ME, Kn_NRC, Kn_RC taken directly from Hofman (1980 CLP),
##        scaled to 2003 CLP using anchor_1950 (asset-specific factor φ_a).
##      * C, NR, T are reconstructed using identities.
##
##  - Output:
##      * Kn_2003.rds  (Kn by asset in 2003 CLP, 1900–1994)
##      * Kn_2003_additivity_residuals.rds (SFC check)
############################################################

library(dplyr)
library(tidyr)
library(here)

source(here("codes","00_setup.R"))  # define dirs, check_additivity(), etc.

dir_int <- here("data","interim")

############################################################
## 1. Cargar insumos
############################################################

raw_clio_Kn  <- readRDS(file.path(dir_int, "raw_clio_Kn.rds"))
raw_hofman_K <- readRDS(file.path(dir_int, "raw_hofman_K.rds"))
anchor_1950  <- readRDS(file.path(dir_int, "anchor_1950.rds"))

# Ventana objetivo del proyecto (ya acordada)
years_pre  <- 1900:1949
years_post <- 1950:1994

############################################################
## 2. FACTORES DE CONVERSIÓN Kn_1980 → Kn_2003 (HOFMAN)
##    Usamos anchor_1950 para obtener φ_a por activo.
############################################################

# Kn en 1980 CLP (Hofman)
kn_1980 <- anchor_1950 %>%
  filter(prices == 1980, year == 1950) %>%
  select(starts_with("Kn_")) %>%
  pivot_longer(
    cols      = everything(),
    names_to  = "asset_raw",
    values_to = "Kn_1980"
  ) %>%
  mutate(asset = sub("^Kn_", "", asset_raw)) %>%
  select(asset, Kn_1980)

# Kn en 2003 CLP (ancla ya convertida)
kn_2003 <- anchor_1950 %>%
  filter(prices == 2003, year == 1950) %>%
  select(starts_with("Kn_")) %>%
  pivot_longer(
    cols      = everything(),
    names_to  = "asset_raw",
    values_to = "Kn_2003"
  ) %>%
  mutate(asset = sub("^Kn_", "", asset_raw)) %>%
  select(asset, Kn_2003)

kn_conv <- kn_1980 %>%
  inner_join(kn_2003, by = "asset") %>%
  mutate(phi = Kn_2003 / Kn_1980)

# Guardamos por si hace falta inspeccionar luego
saveRDS(kn_conv, file.path(dir_int, "Kn_conversion_factors_1950.rds"))

############################################################
## 3. PRE-1950 (1900–1949): Clio escalado a Hofman 1950
############################################################
##  - Usamos Clio solo para ME y C (infraestructura total).
##  - Anclamos niveles a Kn_2003 (1950) de anchor_1950.
##  - NRC, RC se generan con shares de Hofman 1950.

## 3.1. Extraer Clio Kn para ME y C (incluyendo 1950 para base)

clio_backbone <- raw_clio_Kn %>%
  filter(var == "Kn",
         asset %in% c("ME","C"),
         year %in% c(years_pre, 1950)) %>%
  arrange(asset, year)

# Valores base 1950 (índice de Clio)
me_base_1950 <- clio_backbone %>%
  filter(asset == "ME", year == 1950) %>%
  pull(value) %>%
  unique()

c_base_1950 <- clio_backbone %>%
  filter(asset == "C", year == 1950) %>%
  pull(value) %>%
  unique()

if (length(me_base_1950) != 1 | length(c_base_1950) != 1) {
  stop("No se encontraron bases únicas Clio ME/C en 1950.")
}

## 3.2. Anclas Kn_2003(1950) desde anchor_1950

anchor_kn_2003_1950 <- anchor_1950 %>%
  filter(prices == 2003, year == 1950) %>%
  select(Kn_ME, Kn_C, Kn_NRC, Kn_RC)

Kn_ME_2003_1950  <- anchor_kn_2003_1950$Kn_ME
Kn_C_2003_1950   <- anchor_kn_2003_1950$Kn_C
Kn_NRC_2003_1950 <- anchor_kn_2003_1950$Kn_NRC
Kn_RC_2003_1950  <- anchor_kn_2003_1950$Kn_RC

theta_NRC_1950 <- Kn_NRC_2003_1950 / Kn_C_2003_1950
theta_RC_1950  <- Kn_RC_2003_1950  / Kn_C_2003_1950

## 3.3. Construir Kn_ME y Kn_C pre-1950 anclados en 2003 CLP

Kn_ME_pre <- clio_backbone %>%
  filter(asset == "ME", year %in% years_pre) %>%
  mutate(
    value = Kn_ME_2003_1950 * (value / me_base_1950),
    var   = "Kn",
    price_base = "2003_CLP",
    source = "Clio_SK_MAQ_scaled_to_Hofman1950"
  ) %>%
  select(year, asset, var, value, price_base, source)

Kn_C_pre <- clio_backbone %>%
  filter(asset == "C", year %in% years_pre) %>%
  mutate(
    value = Kn_C_2003_1950 * (value / c_base_1950),
    var   = "Kn",
    price_base = "2003_CLP",
    source = "Clio_SK_INF_scaled_to_Hofman1950"
  ) %>%
  select(year, asset, var, value, price_base, source)

## 3.4. Derivar NRC, RC, NR, T usando shares 1950 de Hofman

Kn_pre_wide <- bind_rows(
  Kn_ME_pre %>% select(year, asset, value),
  Kn_C_pre  %>% select(year, asset, value)
) %>%
  tidyr::pivot_wider(names_from = asset, values_from = value) %>%
  mutate(
    NRC = theta_NRC_1950 * C,
    RC  = theta_RC_1950  * C,
    NR  = ME + NRC,
    T   = ME + NRC + RC
  )

Kn_pre_long <- Kn_pre_wide %>%
  pivot_longer(
    cols      = c("ME","NRC","RC","C","NR","T"),
    names_to  = "asset",
    values_to = "value"
  ) %>%
  mutate(
    var        = "Kn",
    price_base = "2003_CLP",
    source     = case_when(
      asset %in% c("ME","C") ~ "Clio_scaled_to_Hofman1950",
      TRUE                   ~ "Clio_scaled + Hofman1950_shares"
    )
  ) %>%
  arrange(year, asset)

############################################################
## 4. 1950–1994: Hofman Kn escalado a 2003 CLP
############################################################
##  - Tomamos ME, NRC, RC en 1980 CLP desde Hofman.
##  - Convertimos a 2003 CLP usando φ_a del ancla 1950.
##  - Reconstituimos C, NR, T por identidades.

hof_kn_prim <- raw_hofman_K %>%
  filter(var == "Kn",
         asset %in% c("ME","NRC","RC"),
         year %in% years_post) %>%
  select(year, asset, value) %>%
  arrange(asset, year)

hof_kn_scaled <- hof_kn_prim %>%
  left_join(kn_conv %>% select(asset, phi), by = "asset") %>%
  mutate(
    value_2003 = value * phi
  ) %>%
  select(year, asset, value = value_2003)

Kn_post_wide <- hof_kn_scaled %>%
  pivot_wider(names_from = asset, values_from = value) %>%
  mutate(
    C  = NRC + RC,
    NR = ME  + NRC,
    T  = ME  + NRC + RC
  )

Kn_post_long <- Kn_post_wide %>%
  pivot_longer(
    cols      = c("ME","NRC","RC","C","NR","T"),
    names_to  = "asset",
    values_to = "value"
  ) %>%
  mutate(
    var        = "Kn",
    price_base = "2003_CLP",
    source     = "Hofman_Kn_scaled_from_1980_to_2003"
  ) %>%
  arrange(year, asset)

############################################################
## 5. Unir pre-1950 y 1950–1994 en panel final
############################################################

Kn_2003 <- bind_rows(
  Kn_pre_long,
  Kn_post_long
) %>%
  arrange(year, asset)

saveRDS(Kn_2003, file.path(dir_int, "Kn_2003.rds"))

############################################################
## 6. Chequeo de aditividad SFC
############################################################

Kn_add <- check_additivity(Kn_2003, "Kn")
saveRDS(Kn_add, file.path(dir_int, "Kn_2003_additivity_residuals.rds"))

message(">>> 05_build_Kn_2003.R COMPLETADO bajo esquema Hofman-dominante + Clio-paths.\n")
############################################################
## FIN
############################################################
