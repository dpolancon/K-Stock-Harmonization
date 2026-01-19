############################################################
## 10_sfc_reconstruction.R
## Stock–Flow Consistent Reconstruction of Kg and Kn
## Window: 1900–1994
## Anchor: 1950
##
## Inputs:
##   - panel_sfc_2003.rds  (Ig, Kg, Kn, delta, z, etc.)
##   - sfc_priors_2003.rds (priors for delta, z, q)
##
## Output:
##   - panel_recon_2003.rds in data/processed/
############################################################

library(dplyr)
library(tidyr)
library(purrr)
library(stringr)
library(here)

## ---------------------------------------------------------
## 0. Paths and Load
## ---------------------------------------------------------
dir_int  <- here("data","interim")
dir_proc <- here("data","processed")
if(!dir.exists(dir_proc)) dir.create(dir_proc, recursive = TRUE)

panel      <- readRDS(file.path(dir_int, "panel_sfc_2003.rds"))
sfc_priors <- readRDS(file.path(dir_int, "sfc_priors_2003.rds"))

priors_delta <- sfc_priors$priors_delta
priors_z     <- sfc_priors$priors_z

## ---------------------------------------------------------
## 1. Define Window and Filter
## ---------------------------------------------------------
year_min    <- 1900
year_anchor <- 1950
year_max    <- 1994

panel_sub <- panel %>%
  filter(year >= year_min, year <= year_max)

assets <- sort(unique(panel_sub$asset))

cat("\n========================================\n")
cat("10_sfc_reconstruction.R — INITIAL SETUP\n")
cat("Reconstruction window: ", year_min, "–", year_max, "\n")
cat("Anchor year: ", year_anchor, "\n")
cat("Assets: ", paste(assets, collapse=", "), "\n")
cat("========================================\n\n")

## ---------------------------------------------------------
## 2. Clean delta & z using priors (p10–p90 clamping + median)
## ---------------------------------------------------------
panel_clean <- panel_sub %>%
  left_join(
    priors_delta %>%
      select(asset,
             delta_low  = plausible_low,
             delta_high = plausible_high,
             delta_med  = median),
    by="asset"
  ) %>%
  left_join(
    priors_z %>%
      select(asset,
             z_low  = plausible_low,
             z_high = plausible_high,
             z_med  = median),
    by="asset"
  ) %>%
  mutate(
    delta_clamped = case_when(
      !is.na(delta) & delta < delta_low  ~ delta_low,
      !is.na(delta) & delta > delta_high ~ delta_high,
      TRUE                               ~ delta
    ),
    z_clamped = case_when(
      !is.na(z) & z < z_low  ~ z_low,
      !is.na(z) & z > z_high ~ z_high,
      TRUE                   ~ z
    ),
    delta_clean = if_else(is.na(delta_clamped), delta_med, delta_clamped),
    z_clean     = if_else(is.na(z_clamped),     z_med,     z_clamped)
  )

cat("Coverage of cleaned rates (delta_clean, z_clean):\n")
print(
  panel_clean %>% group_by(asset) %>%
    summarise(
      n_total = n(),
      n_na_delta = sum(is.na(delta_clean)),
      n_na_z     = sum(is.na(z_clean)),
      .groups="drop"
    )
)
cat("\n")

## ---------------------------------------------------------
## 3. Reconstruction Function (FORWARD + BACKWARD)
## ---------------------------------------------------------
reconstruct_asset <- function(df_asset, anchor_year){
  
  df_asset <- df_asset %>% arrange(year)
  
  if(!(anchor_year %in% df_asset$year)){
    warning("Asset ", unique(df_asset$asset),
            " does not include anchor year ", anchor_year)
    df_asset$Kg_recon <- df_asset$Kn_recon <- NA_real_
    return(df_asset)
  }
  
  idx_anchor <- which(df_asset$year == anchor_year)
  n <- nrow(df_asset)
  
  Kg_rec <- rep(NA_real_, n)
  Kn_rec <- rep(NA_real_, n)
  
  ## Priors fallback = median clean values
  delta_fallback <- median(df_asset$delta_clean, na.rm=TRUE)
  z_fallback     <- median(df_asset$z_clean,     na.rm=TRUE)
  
  ## Use observed stocks at anchor
  Kg_rec[idx_anchor] <- df_asset$Kg[idx_anchor]
  Kn_rec[idx_anchor] <- df_asset$Kn[idx_anchor]
  
  ## ------------------ FORWARD (t+1 … max) ------------------
  if(idx_anchor < n){
    for(i in (idx_anchor+1):n){
      
      Kg_prev <- Kg_rec[i-1]
      Kn_prev <- Kn_rec[i-1]
      Ig_i    <- df_asset$Ig[i]
      
      delta_i <- df_asset$delta_clean[i]
      z_i     <- df_asset$z_clean[i]
      
      if(is.na(delta_i)) delta_i <- delta_fallback
      if(is.na(z_i))     z_i     <- z_fallback
      
      fac_g <- 1 - z_i/1000
      fac_n <- 1 - delta_i/1000
      
      if(any(is.na(c(Kg_prev,Kn_prev,Ig_i))) || fac_g<=0 || fac_n<=0){
        Kg_rec[i] <- Kn_rec[i] <- NA_real_
      } else {
        R_i <- (z_i/1000)*Kg_prev
        D_i <- (delta_i/1000)*Kn_prev
        Kg_rec[i] <- Kg_prev + Ig_i - R_i
        Kn_rec[i] <- Kn_prev + Ig_i - D_i
      }
    }
  }
  
  ## ------------------ BACKWARD (t−1 … min) ------------------
  if(idx_anchor > 1){
    for(i in (idx_anchor-1):1){
      
      j <- i + 1   # use year t=j eqs to recover t−1
      
      Kg_t <- Kg_rec[j]
      Kn_t <- Kn_rec[j]
      Ig_j <- df_asset$Ig[j]
      
      delta_j <- df_asset$delta_clean[j]
      z_j     <- df_asset$z_clean[j]
      
      if(is.na(delta_j)) delta_j <- delta_fallback
      if(is.na(z_j))     z_j     <- z_fallback
      
      fac_g <- 1 - z_j/1000
      fac_n <- 1 - delta_j/1000
      
      if(any(is.na(c(Kg_t,Kn_t,Ig_j))) || fac_g<=0 || fac_n<=0){
        Kg_rec[i] <- Kn_rec[i] <- NA_real_
      } else {
        Kg_rec[i] <- (Kg_t - Ig_j) / fac_g
        Kn_rec[i] <- (Kn_t - Ig_j) / fac_n
      }
    }
  }
  
  df_asset$Kg_recon <- Kg_rec
  df_asset$Kn_recon <- Kn_rec
  
  df_asset
}

## ---------------------------------------------------------
## 4. Apply reconstruction to all assets
## ---------------------------------------------------------
panel_recon <- panel_clean %>%
  group_by(asset) %>%
  group_modify(~ reconstruct_asset(.x, anchor_year=year_anchor)) %>%
  ungroup()

## ---------------------------------------------------------
## 5. Compute Relative Errors vs Observed (1950–1994)
## ---------------------------------------------------------
panel_recon <- panel_recon %>%
  mutate(
    rel_error_Kg = if_else(!is.na(Kg) & !is.na(Kg_recon) & Kg!=0,
                           (Kg_recon - Kg)/Kg, NA_real_),
    rel_error_Kn = if_else(!is.na(Kn) & !is.na(Kn_recon) & Kn!=0,
                           (Kn_recon - Kn)/Kn, NA_real_)
  )

rev_summary <- panel_recon %>%
  filter(year >= year_anchor & year <= year_max) %>%
  group_by(asset) %>%
  summarise(
    mean_rel_Kg = mean(rel_error_Kg, na.rm=TRUE),
    sd_rel_Kg   = sd(rel_error_Kg,   na.rm=TRUE),
    mean_rel_Kn = mean(rel_error_Kn, na.rm=TRUE),
    sd_rel_Kn   = sd(rel_error_Kn,   na.rm=TRUE),
    .groups="drop"
  )

cat("\nRelative error summary (",year_anchor,"–",year_max,"):\n",sep="")
print(rev_summary)
cat("\n")

## ---------------------------------------------------------
## 6. Save output
## ---------------------------------------------------------
saveRDS(panel_recon, file.path(dir_proc,"panel_recon_2003.rds"))

cat("========================================\n")
cat("10_sfc_reconstruction.R COMPLETED\n")
cat("Saved: data/processed/panel_recon_2003.rds\n")
cat("========================================\n\n")
