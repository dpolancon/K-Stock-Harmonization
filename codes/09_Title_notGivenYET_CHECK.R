library(dplyr)
library(tidyr)
library(here)

imp <- readRDS(here("data","processed","sfc_implicit_2003_1900_1994.rds"))

dir_diag <- here("data","diagnostics")
dir.create(dir_diag, showWarnings = FALSE, recursive = TRUE)

# Helpers: gaps relativos (escala-invariante)
out <- imp %>%
  group_by(asset) %>%
  arrange(year, .by_group = TRUE) %>%
  mutate(
    Kg_lag = lag(Kg),
    Kn_lag = lag(Kn),
    
    # gaps relativos (cuando hay denominador)
    gap_R_rel = if_else(!is.na(Kg_lag) & Kg_lag > 0, (R / Kg_lag), NA_real_),
    gap_D_rel = if_else(!is.na(Kn_lag) & Kn_lag > 0, (D / Kn_lag), NA_real_)
  ) %>%
  ungroup()

# 1) Conteo por activo y subperiodo
counts <- out %>%
  mutate(period = case_when(
    year <= 1949 ~ "1900_1949",
    TRUE ~ "1950_1994"
  )) %>%
  group_by(asset, period) %>%
  summarise(
    n = n(),
    n_R_neg = sum(R < 0, na.rm = TRUE),
    n_D_neg = sum(D < 0, na.rm = TRUE),
    share_R_neg = n_R_neg / n,
    share_D_neg = n_D_neg / n,
    .groups = "drop"
  )

# 2) Top años más problemáticos por activo (R más negativo)
top_Rneg <- out %>%
  filter(!is.na(R), R < 0) %>%
  group_by(asset) %>%
  arrange(R, .by_group = TRUE) %>%  # más negativo primero
  slice_head(n = 15) %>%
  ungroup() %>%
  select(asset, year, Ig, Kg_lag, Kg, dKg, R, z, gap_R_rel)

# 3) Los únicos D negativos (para verlos rápido)
all_Dneg <- out %>%
  filter(!is.na(D), D < 0) %>%
  arrange(asset, year) %>%
  select(asset, year, Ig, Kn, dKn, D, delta, gap_D_rel)

# 4) Resumen de severidad: percentiles de R/Kg_lag en los negativos
sev <- out %>%
  filter(!is.na(gap_R_rel), R < 0) %>%
  group_by(asset) %>%
  summarise(
    n_R_neg = n(),
    p5  = quantile(gap_R_rel, 0.05, na.rm = TRUE),
    p25 = quantile(gap_R_rel, 0.25, na.rm = TRUE),
    med = median(gap_R_rel, na.rm = TRUE),
    .groups="drop"
  )

bundle09 <- list(
  meta = list(created_at = Sys.time()),
  counts = counts,
  severity_R = sev,
  top_R_negative = top_Rneg,
  D_negative = all_Dneg
)

stamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
saveRDS(bundle09, file.path(dir_diag, paste0("issue_log_Rneg_Dneg_", stamp, ".rds")))

counts %>% arrange(desc(share_R_neg)) %>% print(n=Inf)
sev %>% arrange(desc(n_R_neg)) %>% print(n=Inf)
top_Rneg %>% arrange(asset, year) %>% print(n=Inf)
all_Dneg %>% print(n=Inf)


by_decade <- out %>%
  mutate(decade = floor(year/10)*10) %>%
  group_by(asset, decade) %>%
  summarise(
    n = n(),
    n_R_neg = sum(R < 0, na.rm=TRUE),
    share_R_neg = n_R_neg/n,
    .groups="drop"
  ) %>%
  arrange(asset, decade)

by_decade %>% print(n=Inf)
