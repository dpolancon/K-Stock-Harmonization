############################################################
## 09_splice_diagnostics.R — TD–SFC COMPLIANT VERSION
## Objetivo:
##   - Detectar discontinuidades en los “splicing years”
##   - Evaluar saltos en Ig, Kg, Kn y tasas derivadas
##   - Comparar 1949→1950 y cualquier otro empalme futuro
##   - Exportar:
##       * splice_jumps_by_asset.rds
##       * splice_flags.rds
##       * splice_summary.rds
############################################################

library(dplyr)
library(tidyr)
library(purrr)
library(here)

source(here("codes", "00_setup.R"))

############################################################
## 1. Cargar panel SFC
############################################################

panel <- readRDS(file.path(dir_data_interim, "panel_sfc_2003.rds"))

req <- c("year","asset","Ig","Kg","Kn","delta","z","i","FNKF")
if (!all(req %in% names(panel))) {
  stop("09_splice_diagnostics: faltan columnas requeridas en panel_sfc_2003.rds.")
}

assets <- sort(unique(panel$asset))

############################################################
## 2. Definir años de empalme (“splice years”)
##    Para este proyecto: 1950 es seguro.
##    Pero dejamos el sistema abierto.
############################################################

# Detectar automáticamente momentos donde alguna fuente cambia régimen
candidate_splice_years <- c(1950)   # base manual

splice_years <- sort(unique(candidate_splice_years))

if (length(splice_years) == 0) {
  stop("No splice years defined. Add at least 1950.")
}

############################################################
## 3. Función para computar saltos  t0→t1
############################################################

compute_jump <- function(df, var_name, t0, t1) {
  v0 <- df %>% filter(year == t0) %>% pull(!!sym(var_name))
  v1 <- df %>% filter(year == t1) %>% pull(!!sym(var_name))
  
  if (length(v0) == 0 | length(v1) == 0) return(NULL)
  
  tibble(
    year_pre  = t0,
    year_post = t1,
    var       = var_name,
    level_pre = v0,
    level_post = v1,
    jump_abs  = v1 - v0,
    jump_pct  = ifelse(!is.na(v0) & v0 != 0, (v1 - v0)/v0, NA_real_)
  )
}

############################################################
## 4. Construir tabla de saltos para todas las variables
############################################################

vars_to_test <- c("Ig","Kg","Kn","delta","z","i","FNKF")

splice_jumps <- map_dfr(
  splice_years,
  function(syear) {
    t0 <- syear - 1
    t1 <- syear
    
    map_dfr(
      assets,
      function(a) {
        df_a <- panel %>% filter(asset == a)
        
        map_dfr(
          vars_to_test,
          function(v) {
            compute_jump(df_a, v, t0, t1) %>%
              mutate(asset = a)
          }
        )
      }
    )
  }
)

saveRDS(
  splice_jumps,
  file.path(dir_data_interim, "splice_jumps_by_asset.rds")
)

############################################################
## 5. Definir umbrales para detectar “saltos problemáticos”
############################################################

threshold_pct <- list(
  Ig   = 0.50,     # ±50% jump is suspicious
  Kg   = 0.15,     # capital stock normally smooth; 15% jump is large
  Kn   = 0.15,
  delta = 0.30,    # depreciation rate shouldn't swing wildly
  z     = 0.30,
  i     = 0.40,
  FNKF  = 0.50
)

############################################################
## 6. Generar flags de discontinuidad
############################################################

splice_flags <- splice_jumps %>%
  mutate(
    thr = map_dbl(var, ~ threshold_pct[[.x]])
  ) %>%
  rowwise() %>%
  mutate(
    flag_jump = ifelse(!is.na(jump_pct) & abs(jump_pct) > thr, TRUE, FALSE)
  ) %>%
  ungroup()

############################################################
## 7. BUILD SPLICE SUMMARY TABLE (AGGREGATED)
############################################################

splice_summary <- splice_flags %>%
  group_by(year_pre, year_post, var) %>%
  summarise(
    n_assets      = n(),
    n_flags       = sum(flag_jump, na.rm = TRUE),
    max_jump_pct  = max(abs(jump_pct), na.rm = TRUE),
    worst_asset   = asset[which.max(abs(jump_pct))],
    worst_jump    = jump_pct[which.max(abs(jump_pct))],
    .groups = "drop"
  )

saveRDS(splice_summary, file.path(dir_data_interim, "splice_summary.rds"))

message("splice_summary.rds exported.") 
############################################################
## FIN
############################################################
