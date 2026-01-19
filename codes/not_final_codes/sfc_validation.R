############################################################
## 07_SFC_validation.R  (VERSIÓN CORREGIDA)
## Proyecto: Stock–flow consistent capital stock reconstruction (Chile)
##
## Tareas unificadas:
##  - Cargar panel_sfc_2003.rds
##  - Plots diagnósticos (delta, z, residuales) con líneas de empalme
##  - Exportar panel completo (RDS + CSV)
##  - Índices de validación por activos y períodos
##  - Índices globales
##  - PCA perfiles delta/z + clustering
##  - Identificar outliers
##  - Exportación en CSV + tablas TEX (paper y apéndice)
############################################################

###############
## 0. Setup
###############
library(dplyr)
library(tidyr)
library(readr)
library(ggplot2)
library(stringr)
library(here)
library(knitr)
library(kableExtra)

source(here("codes", "00_setup.R"))

## Directorios de salida
dir_fig_sfc   <- here("outputs", "figures", "sfc")
dir_tab_paper <- here("outputs", "tables",  "paper")
dir_tab_appx  <- here("outputs", "tables",  "appendix")
dir_tab_csv   <- here("outputs", "tables",  "csv_backups")

dir.create(dir_fig_sfc,   recursive = TRUE, showWarnings = FALSE)
dir.create(dir_tab_paper, recursive = TRUE, showWarnings = FALSE)
dir.create(dir_tab_appx,  recursive = TRUE, showWarnings = FALSE)
dir.create(dir_tab_csv,   recursive = TRUE, showWarnings = FALSE)

###############
## 1. Load SFC Panel
###############
panel_file <- file.path(dir_data_interim, "panel_sfc_2003.rds")
if (!file.exists(panel_file)) stop("panel_sfc_2003.rds no encontrado.")

panel_sfc <- readRDS(panel_file)

cat("\n==============================\n")
cat("  07_SFC_validation iniciado\n")
cat("==============================\n\n")

###############
## 2. Chequeo de columnas mínimas
###############
req_cols <- c(
  "year","asset","Ig","Kg","Kn",
  "dKg","dKn","D","R","delta","z",
  "eps_joint","r_joint_Ig","r_joint_Kg","r_joint_Kn",
  "period","full_SFC_window","full_ME_window"
)

missing <- setdiff(req_cols, names(panel_sfc))
if (length(missing) > 0) stop("Faltan columnas: ", paste(missing, collapse=", "))

###############
## 3. Función de líneas de empalme
###############
splice_years <- c(1900, 1940, 1950, 1994)

## FIX: definir como capa ggplot, no como función
add_splice_lines <- geom_vline(
  xintercept = splice_years,
  linetype   = "dashed",
  alpha      = 0.4
)

###############
## 4. PLOTS DIAGNÓSTICOS
###############

## 4.1 Depreciación implícita
p_delta <- panel_sfc %>%
  filter(!is.na(delta)) %>%
  ggplot(aes(x = year, y = delta)) +
  geom_line() +
  facet_wrap(~ asset, scales = "free_y") +
  add_splice_lines +
  labs(
    title = "Implicit Depreciation Rate (\delta_t = D_t / Kn_t)",
    y = "d (annual rate)", x = "Year"
  ) +
  theme_minimal()

ggsave(file.path(dir_fig_sfc, "delta_by_asset.png"), p_delta, width=11, height=7)

## 4.2 Tasa de retiro/depleción
p_z <- panel_sfc %>%
  filter(!is.na(z)) %>%
  ggplot(aes(x = year, y = z)) +
  geom_line() +
  facet_wrap(~ asset, scales = "free_y") +
  add_splice_lines +
  labs(
    title = "Retirement Rate / depletion (z_t = R_t / Kg_t)",
    y = "z (annual rate)", x = "Year"
  ) +
  theme_minimal()

ggsave(file.path(dir_fig_sfc, "z_by_asset.png"), p_z, width=11, height=7)

## 4.3 Residuo SFC normalizado
p_rIg <- panel_sfc %>%
  filter(!is.na(r_joint_Ig)) %>%
  ggplot(aes(x = year, y = r_joint_Ig)) +
  geom_hline(yintercept=0, alpha=.6) +
  geom_line() +
  facet_wrap(~ asset, scales="free_y") +
  add_splice_lines +
  labs(
    title="Joint SFC residual normalizado (r_joint_Ig)",
    y="eps_joint / Ig", x="Año"
  ) +
  theme_minimal()

ggsave(file.path(dir_fig_sfc, "r_joint_Ig_by_asset.png"), p_rIg, width=11, height=7)

###############
## 5. Exportación del panel
###############
saveRDS(panel_sfc, file.path(dir_data_processed, "panel_sfc_2003.rds"))
write_csv(panel_sfc, file.path(dir_data_processed, "panel_sfc_2003.csv"))

## Panel reducido para regresiones
reg_panel <- panel_sfc %>%
  select(year, asset, Ig, Kg, Kn, D, R, delta, z) %>%
  arrange(asset, year)

saveRDS(reg_panel, file.path(dir_data_processed, "panel_sfc_2003_regression.rds"))
write_csv(reg_panel, file.path(dir_data_processed, "panel_sfc_2003_regression.csv"))

###############
## 6. Índices de validación por activo y período
###############
residual_stats <- panel_sfc %>%
  group_by(asset, period) %>%
  summarise(
    MSE_rIg     = mean(r_joint_Ig^2, na.rm=TRUE),
    RMSE_rIg    = sqrt(MSE_rIg),
    MAE_rIg     = mean(abs(r_joint_Ig), na.rm=TRUE),
    max_abs_rIg = max(abs(r_joint_Ig), na.rm=TRUE),
    p_small_2   = mean(abs(r_joint_Ig) <= 0.02, na.rm=TRUE),
    p_small_5   = mean(abs(r_joint_Ig) <= 0.05, na.rm=TRUE),
    n_obs       = sum(!is.na(r_joint_Ig)),
    .groups="drop"
  )

rate_stats <- panel_sfc %>%
  group_by(asset, period) %>%
  summarise(
    mean_delta = mean(delta, na.rm=TRUE),
    sd_delta   = sd(delta,   na.rm=TRUE),
    cv_delta   = sd_delta / abs(mean_delta),
    mean_z     = mean(z, na.rm=TRUE),
    sd_z       = sd(z,   na.rm=TRUE),
    cv_z       = sd_z / abs(mean_z),
    n_delta    = sum(!is.na(delta)),
    n_z        = sum(!is.na(z)),
    .groups="drop"
  )

###############
## 7. Exportación Tablas TEX + CSV
###############

## --- paper tables ---
kable(residual_stats, format="latex", booktabs=TRUE) %>%
  kable_styling(full_width=FALSE) %>%
  save_kable(file.path(dir_tab_paper, "residual_stats.tex"))

kable(rate_stats, format="latex", booktabs=TRUE) %>%
  kable_styling(full_width=FALSE) %>%
  save_kable(file.path(dir_tab_paper, "rate_stats.tex"))

## --- appendix (detallado) ---
write_csv(residual_stats, file.path(dir_tab_csv, "residual_stats.csv"))
write_csv(rate_stats,     file.path(dir_tab_csv, "rate_stats.csv"))

############################################################
## 8. PCA + CLUSTERING + EXPORTS (paper + appendix)
############################################################

cat(">>> PCA + clustering: inicio <<<\n")

# -------------------------
# 8.0 Data cleaning
# -------------------------
pca_input <- panel_sfc %>%
  filter(full_SFC_window) %>%
  select(asset, year, delta, z) %>%
  mutate(
    delta = ifelse(is.finite(delta), delta, NA_real_),
    z     = ifelse(is.finite(z),     z,     NA_real_)
  ) %>%
  drop_na(delta, z)

if (nrow(pca_input) < 5) stop("Insuficientes datos válidos para PCA.")

# -------------------------
# 8.1 PCA (delta, z)
# -------------------------
pca_res <- stats::prcomp(
  pca_input %>% select(delta, z),
  scale = TRUE
)

pca_scores <- as.data.frame(pca_res$x) %>%
  mutate(asset = pca_input$asset, year = pca_input$year)

pca_loadings <- as.data.frame(pca_res$rotation)

# TEX export — appendix
sink(file.path(dir_tab_appx, "pca_summary.tex"))
print(knitr::kable(
  summary(pca_res)$importance,
  format="latex",
  booktabs=TRUE,
  caption="PCA summary: variance explained (delta, z)"
))
sink()

sink(file.path(dir_tab_appx, "pca_loadings.tex"))
print(knitr::kable(
  pca_loadings,
  format="latex",
  booktabs=TRUE,
  caption="PCA loadings for delta and z"
))
sink()

# -------------------------
# 8.2 PCA scatter for appendix
# -------------------------
p_pca <- ggplot(pca_scores, aes(x = PC1, y = PC2, colour = asset)) +
  geom_point(alpha=0.7) +
  theme_minimal() +
  labs(
    title = "PCA scatter (delta, z)",
    subtitle = "Full SFC window (1950–1994)",
    x = "PC1", y = "PC2"
  )

ggsave(
  filename = file.path(dir_fig_sfc, "pca_scatter.png"),
  plot     = p_pca,
  width = 7, height = 5
)

# -------------------------
# 8.3 K-means clustering (k=3)
# -------------------------
set.seed(123)
km <- kmeans(pca_scores %>% select(PC1, PC2), centers = 3)

pca_scores$cluster_km <- factor(km$cluster)

# TEX table for paper (summary of clusters)
cluster_summary <- pca_scores %>%
  group_by(cluster_km, asset) %>%
  summarise(n_obs = n(), .groups="drop")

sink(file.path(dir_tab_paper, "clusters_kmeans_assets.tex"))
print(knitr::kable(
  cluster_summary,
  format="latex",
  booktabs=TRUE,
  caption="Cluster membership (K-means, k=3)"
))
sink()

# Scatter with clusters — appendix
p_km <- ggplot(pca_scores, aes(PC1, PC2, colour=cluster_km, shape=asset)) +
  geom_point(size=2) +
  theme_minimal() +
  labs(title="K-means clusters on PCA space")

ggsave(
  filename = file.path(dir_fig_sfc, "pca_kmeans_clusters.png"),
  plot     = p_km,
  width=7, height=5
)

# -------------------------
# 8.4 Hierarchical clustering
# -------------------------
dist_mat <- dist(pca_scores %>% select(PC1, PC2))
hc <- hclust(dist_mat, method="ward.D2")

# Export dendrogram
png(file.path(dir_fig_sfc, "hclust_dendrogram.png"),
    width=800, height=600)
plot(hc, main="Hierarchical clustering dendrogram", xlab="", sub="")
dev.off()

# Cut tree into 3 clusters
pca_scores$cluster_hc <- factor(cutree(hc, k=3))

# TEX table — appendix
hc_summary <- pca_scores %>%
  group_by(cluster_hc, asset) %>%
  summarise(n_obs=n(), .groups="drop")

sink(file.path(dir_tab_appx, "clusters_hclust_assets.tex"))
print(knitr::kable(
  hc_summary,
  format="latex",
  booktabs=TRUE,
  caption="Hierarchical clustering membership (Ward, k=3)"
))
sink()

cat(">>> PCA + clustering: COMPLETADO <<<\n\n")


###############
## 9. Outliers
###############
outliers <- panel_sfc %>%
  filter(
    abs(r_joint_Ig) > 0.1 |
      delta > quantile(delta, .99, na.rm=TRUE) |
      z     > quantile(z, .99, na.rm=TRUE)
  )

write_csv(outliers, file.path(dir_tab_appx, "sfc_outliers.csv"))

###############
## FINAL
###############
cat("\n>>> 07_SFC_validation COMPLETADO <<<\n")
