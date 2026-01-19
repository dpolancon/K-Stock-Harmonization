  ############################################################
  ## 10_export_validation_materials.R
  ## Exports LaTeX tables + validation plots
  ## Folder structure:
  ## outputs/
  ##   validation/
  ##     tables/
  ##       sfc_rate_summary.tex
  ##       splice_summary_1950.tex
  ##       splice_worst_jumps.tex
  ##     plots/
  ##       delta_timeseries.pdf
  ##       z_timeseries.pdf
  ##       i_timeseries.pdf
  ##       splice_jump_Ig.pdf
  ##       splice_jump_Kg.pdf
  ##       splice_jump_Kn.pdf
  ##       splice_jump_delta.pdf
  ##       splice_jump_z.pdf
  ##       splice_jump_i.pdf
  ##       splice_jump_FNKF.pdf
  ##       additivity_Ig.pdf
  ##       additivity_Kg.pdf
  ##       additivity_Kn.pdf
  ############################################################
  
  
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(purrr)
  library(here)
  
  suppressWarnings({
    have_knitr      <- requireNamespace("knitr", quietly = TRUE)
    have_kableExtra <- requireNamespace("kableExtra", quietly = TRUE)
  })
  
  dir_int      <- here("data", "interim")
  dir_out_val  <- here("outputs", "validation")
  dir_tables   <- file.path(dir_out_val, "tables")
  dir_plots    <- file.path(dir_out_val, "plots")
  
  dir.create(dir_out_val, recursive = TRUE, showWarnings = FALSE)
  dir.create(dir_tables,  recursive = TRUE, showWarnings = FALSE)
  dir.create(dir_plots,   recursive = TRUE, showWarnings = FALSE)
  
  ############################################################
  ## 0. Helper: round_df()  (non-scientific, 3 decimals)
  ############################################################
  
  round_df <- function(df, digits = 2) {
    df %>%
      mutate(across(
        where(is.numeric),
        ~ formatC(.x, format = "f", digits = digits)
      ))
  }
  
  ############################################################
  ## Helper: table_as_is()  (patched)
  ############################################################
  
  table_as_is <- function(data, file_path,
                          column_labels = NULL,
                          caption = "Table",
                          format = c("latex", "html"),
                          overwrite = TRUE,
                          escape = TRUE,
                          return_string = FALSE,
                          footnote = NULL,
                          manifest_hook = NULL) {
    
    format <- match.arg(format)
    
    if (!is.data.frame(data) && !is.matrix(data))
      stop("`data` must be a data.frame or matrix.")
    
    if (!is.null(column_labels)) {
      if (length(column_labels) != ncol(data))
        stop("column_labels length mismatch.")
      colnames(data) <- column_labels
    }
    
    dir_path <- dirname(file_path)
    if (!dir.exists(dir_path))
      dir.create(dir_path, recursive = TRUE, showWarnings = FALSE)
    
    if (file.exists(file_path) && !isTRUE(overwrite))
      stop("File exists and overwrite = FALSE: ", file_path)
    
    if (!have_knitr)
      stop("Package 'knitr' is required for table_as_is().")
    
    # kable only — NO threeparttable or tablenotes
    tbl <- knitr::kable(data,
                        format = format,
                        booktabs = TRUE,
                        caption = caption,
                        escape = escape)
    
    if (have_kableExtra) {
      if (format == "latex") {
        tbl <- kableExtra::kable_styling(tbl, latex_options = c("hold_position"))
      } else {
        tbl <- kableExtra::kable_styling(tbl, bootstrap_options = c("condensed","responsive"))
      }
      tbl_string <- as.character(tbl)
    } else {
      tbl_string <- paste(tbl, collapse = "\n")
    }
    
    if (isTRUE(return_string)) return(tbl_string)
    
    tryCatch({
      writeLines(tbl_string, con = file_path, useBytes = TRUE)
      if (is.function(manifest_hook))
        manifest_hook(list(type = "table", file = file_path, caption = caption))
      invisible(file_path)
    }, error = function(e) stop("Failed to write table: ", conditionMessage(e)))
  }
  
  ############################################################
  ## 1. Load main objects
  ############################################################
  
  panel            <- readRDS(file.path(dir_int, "panel_sfc_2003.rds"))
  sfc_rate_summary <- readRDS(file.path(dir_int, "sfc_rate_summary.rds"))
  splice_summary   <- readRDS(file.path(dir_int, "splice_summary.rds"))
  splice_jumps     <- readRDS(file.path(dir_int, "splice_jumps_by_asset.rds"))
  
  Ig_add <- readRDS(file.path(dir_int, "Ig_2003_additivity_residuals.rds"))
  Kg_add <- readRDS(file.path(dir_int, "Kg_2003_additivity_residuals.rds"))
  Kn_add <- readRDS(file.path(dir_int, "Kn_2003_additivity_residuals.rds"))
  
  
  
  ############################################################
  ## Build THREE clean tables instead of one mega-table
  ############################################################
  
  # 1. Depreciation & Depletion
  ############################################################
  ## Build THREE clean tables instead of one mega-table
  ############################################################
  
  # 1. Depreciation 
  table_dep_d <- sfc_rate_summary %>%
    select(
      asset, n_obs,
      delta_min, delta_p10, delta_med, delta_mean, delta_p90, delta_max,
    ) %>%
    round_df(2)

  # 2. Depletion
  
  table_dep_z <- sfc_rate_summary %>%
    select(
      asset, n_obs,
      z_min, z_p10, z_med, z_mean, z_p90, z_max) %>%
    round_df(2)
  
  
  # 3. Investment ratio (i)
  table_i <- sfc_rate_summary %>%
    select(
      asset, n_obs,
      i_min, i_med, i_mean, i_max
    ) %>%
    round_df(2)
  
  # 4. FNKF 
  table_fnkf <- sfc_rate_summary %>%
    select(
      asset, n_obs,
      FNKF_min, FNKF_med, FNKF_mean, FNKF_max
    ) %>%
    round_df(2)
  
  # 5.Kn/Kg  
  table_knkg <- sfc_rate_summary %>%
    select(
      asset, n_obs,
      KnKg_min, KnKg_med, KnKg_mean, KnKg_max
      ) %>%
    round_df(2)
  
  # 6. SFC esp residuals  
  table_eps <- sfc_rate_summary %>%
    select(
      asset, n_obs,    
      epsKg_mean, epsKn_mean, epsJoint_mean
    ) %>%
    round_df(2)
    
  ############################################################
  ## 2. Export LaTeX tables (rounded to 3 decimals)
  ############################################################
  
  ## 2.1 SFC Rate Summary
  table_as_is(
    table_dep_d,
    file.path(dir_tables, "sfc_rates_dep_d.tex"),
    caption = "Depreciation  Rates"
  )
  
  table_as_is(
    table_dep_z,
    file.path(dir_tables, "sfc_rates_dep_z.tex"),
    caption = "Depletition Rates"
  )
  
  table_as_is(
    table_i,
    file.path(dir_tables, "sfc_rates_i.tex"),
    caption = "Investment–Capital Ratios"
  )
  
  table_as_is(
    table_fnkf,
    file.path(dir_tables, "sfc_rates_fnkf.tex"),
    caption = "Net Fixed Capital Formation"
  )
  
  table_as_is(
    table_knkg,
    file.path(dir_tables, "sfc_rates_knkg.tex"),
    caption = "Kn/Kg Ratios"
  )

  table_as_is(
    table_eps,
    file.path(dir_tables, "sfc_rates_eps.tex"),
    caption = "SFC Residuals"
  )
  
  
  ## 2.2 Splice summary for 1949→1950
  splice_summary_1950 <- splice_summary %>%
    filter(year_pre == 1949, year_post == 1950)
  
  table_as_is(
    data        = round_df(splice_summary_1950, 2),
    file_path   = file.path(dir_tables, "splice_summary_1950.tex"),
    caption     = "Splice diagnostics for 1949 to 1950",
    format      = "latex",
    overwrite   = TRUE
  )
  
  ## 2.3 Worst jumps across all variables
  splice_worst <- splice_jumps %>%
    group_by(var, asset) %>%
    slice_max(abs(jump_pct), n = 1, with_ties = FALSE) %>%
    ungroup()
  
  table_as_is(
    data        = round_df(splice_worst, 2),
    file_path   = file.path(dir_tables, "splice_worst_jumps.tex"),
    caption     = "Largest splice discontinuities across variables",
    format      = "latex",
    overwrite   = TRUE
  )
  
  ## 2.4 Additivity residual tables
  table_as_is(round_df(Ig_add, 2), file.path(dir_tables,"additivity_Ig.tex"),
              caption="Additivity residuals: Ig", format="latex")
  
  table_as_is(round_df(Kg_add, 2), file.path(dir_tables,"additivity_Kg.tex"),
              caption="Additivity residuals: Kg", format="latex")
  
  table_as_is(round_df(Kn_add, 2), file.path(dir_tables,"additivity_Kn.tex"),
              caption="Additivity residuals: Kn", format="latex")
  
  ############################################################
  ## 3. Plot helper: rate time series with linear + LOESS
  ############################################################
  
  plot_rate <- function(df, yvar, title, outfile) {
    
    p <- ggplot(df, aes(x = year, y = !!sym(yvar), color = asset)) +
      geom_line(size = 0.8, alpha = 0.85) +
      theme_minimal(base_size = 12) +
      labs(
        title = paste0(title, "Rate"),
        x = NULL,
        y = NULL
      ) +
      theme(
        legend.position = "bottom",
        plot.title = element_text(size = 13, face = "bold")
      )
    
    ggsave(file.path(dir_plots, outfile), p, width = 9, height = 4.8)
  }
  
  
  ############################################################
  ## 4. Export main rate time-series plots (δ, z, i)
  ############################################################
  
  plot_rate(
    panel %>% filter(!is.na(delta)),
    "delta",
    "Implicit Depreciation Rate \\delta_t",
    "delta_timeseries.pdf"
  )
  
  plot_rate(
    panel %>% filter(!is.na(z)),
    "z",
    "Implicit Depletion Rate z_t",
    "z_timeseries.pdf"
  )
  
  plot_rate(
    panel %>% filter(!is.na(i)),
    "i",
    "Investment–Capital Ratio i_t",
    "i_timeseries.pdf"
  )
  
  ############################################################
  ## 5. Splice jump plots for 1949→1950 (Ig, Kg, Kn, δ, z, i, FNKF)
  ############################################################
  
  plot_splice_var <- function(splice_df, var_name, outfile) {
    df_var <- splice_df %>%
      filter(var == var_name, year_pre == 1949, year_post == 1950)
    
    if (nrow(df_var) == 0) return(invisible(NULL))
    
    p <- ggplot(df_var, aes(x = asset, y = jump_pct)) +
      geom_hline(yintercept = 0, linetype = "dotted") +
      geom_col(alpha = 0.8) +
      theme_minimal(base_size = 12) +
      labs(
        title = paste0("Splice jump 1949→1950: ", var_name),
        x = "Asset",
        y = "Relative jump (fractional change)"
      ) +
      theme(
        axis.text.x = element_text(angle = 45, hjust = 1)
      )
    
    ggsave(file.path(dir_plots, outfile), p, width = 7.5, height = 4.5)
  }
  
  plot_splice_var(splice_jumps, "Ig",   "splice_jump_Ig.pdf")
  plot_splice_var(splice_jumps, "Kg",   "splice_jump_Kg.pdf")
  plot_splice_var(splice_jumps, "Kn",   "splice_jump_Kn.pdf")
  plot_splice_var(splice_jumps, "delta","splice_jump_delta.pdf")
  plot_splice_var(splice_jumps, "z",    "splice_jump_z.pdf")
  plot_splice_var(splice_jumps, "i",    "splice_jump_i.pdf")
  plot_splice_var(splice_jumps, "FNKF", "splice_jump_FNKF.pdf")
  
  ############################################################
  ## 6. Additivity residual plots (Ig, Kg, Kn)
  ############################################################
  
  plot_additivity_residuals <- function(add_df, title, outfile) {
    # Expect columns: year, res_NR, res_C, res_T (from check_additivity)
    res_long <- add_df %>%
      select(year, starts_with("res_")) %>%
      pivot_longer(
        cols = starts_with("res_"),
        names_to = "identity",
        values_to = "residual"
      )
    
    p <- ggplot(res_long, aes(x = year, y = residual, color = identity)) +
      geom_hline(yintercept = 0, linetype = "dotted") +
      geom_line(size = 0.7) +
      theme_minimal(base_size = 12) +
      labs(
        title = title,
        x = NULL,
        y = "Additivity residual"
      ) +
      theme(
        legend.position = "bottom",
        plot.title = element_text(size = 13, face = "bold")
      )
    
    ggsave(file.path(dir_plots, outfile), p, width = 8, height = 4.5) }
  
  plot_additivity_residuals(
    Ig_add,
    "Additivity residuals for Ig (C, NR, T identities)",
    "additivity_Ig.pdf"
  )
  
  plot_additivity_residuals(
    Kg_add,
    "Additivity residuals for Kg (C, NR, T identities)",
    "additivity_Kg.pdf"
  )
  
  plot_additivity_residuals(
    Kn_add,
    "Additivity residuals for Kn (C, NR, T identities)",
    "additivity_Kn.pdf"
  )
  
  ############################################################
  ## Done
  ############################################################
  
  message(">>> Validation materials exported to: ", dir_out_val)
  message("    - Tables in: ", dir_tables)
  message("    - Plots  in: ", dir_plots)
