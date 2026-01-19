############################################################
## 09_sfc_extended_reports_v2.R
## Reportes avanzados de priors SFC: δ, z, q, outliers
## Salidas en: outputs/priors/
## Incluye FIX crítico: sanitización de delta_outlier y z_outlier
############################################################

library(dplyr)
library(tidyr)
library(ggplot2)
library(purrr)
library(stringr)
library(here)

## ---------------------------------------------------------
## 0. Paths
## ---------------------------------------------------------
dir_int  <- here("data","interim")
dir_out  <- here("outputs","priors")

if(!dir.exists(dir_out)) dir.create(dir_out, recursive = TRUE)

sfc_priors <- readRDS(file.path(dir_int,"sfc_priors_2003.rds"))
panel      <- readRDS(file.path(dir_int,"panel_sfc_2003.rds"))

priors_delta <- sfc_priors$priors_delta
priors_z     <- sfc_priors$priors_z
priors_q     <- sfc_priors$priors_q
outliers     <- sfc_priors$outliers

assets <- sort(unique(panel$asset))

## ---------------------------------------------------------
## FIX: Sanitizar las columnas delta_outlier y z_outlier
## ---------------------------------------------------------
clean_attr <- function(x){
  attributes(x) <- NULL
  x
}

outliers <- outliers %>%
  mutate(
    delta_outlier = clean_attr(as.logical(delta_outlier)),
    z_outlier     = clean_attr(as.logical(z_outlier))
  )

## ---------------------------------------------------------
## Helper de guardado
## ---------------------------------------------------------
save_plot <- function(g, name, w=8, h=5){
  ggsave(filename = file.path(dir_out, paste0(name,".png")),
         plot = g, width = w, height = h, dpi = 300)
}

period_colors <- c(
  "1900_1949" = "#984ea3",
  "1950_1994" = "#4daf4a",
  "1995_plus" = "#377eb8"
)

############################################################
## 1. Histogramas y densidades de δ y z por activo
############################################################
for(a in assets){
  
  df <- panel %>% filter(asset == a, !is.na(delta), !is.na(z))
  
  ## --- δ ---
  g1 <- ggplot(df, aes(x = delta, fill = period)) +
    geom_histogram(alpha = 0.6, bins = 40, position="identity") +
    scale_fill_manual(values = period_colors) +
    labs(title = paste("Distribución δ_t – Activo:", a),
         x = "δ_t (implicada)", y = "Frecuencia") +
    theme_minimal()
  
  save_plot(g1, paste0("delta_hist_", a))
  
  g2 <- ggplot(df, aes(x = delta, color = period)) +
    geom_density(size = 1.2) +
    scale_color_manual(values = period_colors) +
    labs(title = paste("Densidad δ_t por período –", a),
         x = "δ_t") +
    theme_minimal()
  
  save_plot(g2, paste0("delta_density_", a))
  
  ## --- z ---
  g3 <- ggplot(df, aes(x = z, fill = period)) +
    geom_histogram(alpha = 0.6, bins = 40, position="identity") +
    scale_fill_manual(values = period_colors) +
    labs(title = paste("Distribución z_t – Activo:", a),
         x = "z_t (retiros implícitos)", y = "Frecuencia") +
    theme_minimal()
  
  save_plot(g3, paste0("z_hist_", a))
  
  g4 <- ggplot(df, aes(x = z, color = period)) +
    geom_density(size = 1.2) +
    scale_color_manual(values = period_colors) +
    labs(title = paste("Densidad z_t por período –", a),
         x = "z_t") +
    theme_minimal()
  
  save_plot(g4, paste0("z_density_", a))
}

############################################################
## 2. Trayectorias temporales δ, z y q con bandas prior p10–p90
############################################################
for(a in assets){
  
  df <- panel %>% filter(asset == a)
  
  d_lo <- priors_delta %>% filter(asset == a) %>% pull(plausible_low)
  d_hi <- priors_delta %>% filter(asset == a) %>% pull(plausible_high)
  
  z_lo <- priors_z %>% filter(asset == a) %>% pull(plausible_low)
  z_hi <- priors_z %>% filter(asset == a) %>% pull(plausible_high)
  
  ## δ_t
  g5 <- ggplot(df, aes(year, delta)) +
    geom_line(alpha=0.8) +
    geom_hline(yintercept = d_lo, color="red", linetype="dashed") +
    geom_hline(yintercept = d_hi, color="red", linetype="dashed") +
    labs(title=paste("δ_t con bandas prior –", a), y="δ_t") +
    theme_minimal()
  
  save_plot(g5, paste0("delta_time_", a))
  
  ## z_t
  g6 <- ggplot(df, aes(year, z)) +
    geom_line(alpha=0.8, color="black") +
    geom_hline(yintercept = z_lo, color="red", linetype="dashed") +
    geom_hline(yintercept = z_hi, color="red", linetype="dashed") +
    labs(title=paste("z_t con bandas prior –", a), y="z_t") +
    theme_minimal()
  
  save_plot(g6, paste0("z_time_", a))
  
  ## q_t = Kg/Kn
  df <- df %>% mutate(q = Kg / Kn)
  
  q_stats <- priors_q %>% filter(asset == a)
  
  g7 <- ggplot(df, aes(year, q)) +
    geom_line() +
    geom_hline(yintercept = q_stats$plausible_low_q, linetype="dashed", color="blue") +
    geom_hline(yintercept = q_stats$plausible_high_q, linetype="dashed", color="blue") +
    labs(title=paste("Razón q = Kg/Kn –", a), y="q_t") +
    theme_minimal()
  
  save_plot(g7, paste0("q_time_", a))
}

############################################################
## 3. Correlaciones δ, z, dKg, dKn
############################################################
corr_dir <- file.path(dir_out, "correlations")
if(!dir.exists(corr_dir)) dir.create(corr_dir)

for(a in assets){
  df <- panel %>%
    filter(asset == a) %>%
    select(delta, z, dKg, dKn) %>%
    filter(if_all(everything(), ~ !is.na(.x)))
  
  if(nrow(df) > 5){
    cmat <- cor(df)
    write.csv(cmat, file.path(corr_dir, paste0("corr_", a, ".csv")),
              row.names=TRUE)
  }
}

############################################################
## 4. Plano δ–z con outliers FIXED
############################################################
for(a in assets){
  
  df <- panel %>% filter(asset == a) %>%
    left_join(outliers %>% select(year, asset, delta_outlier, z_outlier),
              by=c("year","asset"))
  
  ## Clasificación final
  df <- df %>%
    mutate(
      out_type = case_when(
        delta_outlier & z_outlier ~ "Ambos",
        delta_outlier             ~ "Delta",
        z_outlier                 ~ "Z",
        TRUE                      ~ "OK"
      )
    )
  
  g8 <- ggplot(df, aes(delta, z, color=out_type)) +
    geom_point(alpha=0.7, size=2) +
    scale_color_manual(values=c(
      "OK"="grey60",
      "Delta"="red",
      "Z"="blue",
      "Ambos"="purple"
    )) +
    labs(
      title=paste("Plano δ–z con outliers –", a),
      x="δ_t", y="z_t"
    ) +
    theme_minimal()
  
  save_plot(g8, paste0("delta_z_plane_", a))
}

message(">>> 09_sfc_extended_reports_v2 COMPLETADO <<<")
