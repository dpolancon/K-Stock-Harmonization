# ==============================================================================
# Journal-Standard Capital Stock Rate Plots Generator (R / ggplot2)
# Protocol: NO titles, subtitles, or notes inside plot images (handled in LaTeX).
# ==============================================================================

library(ggplot2)
library(readr)
library(dplyr)

csv_path <- "outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_master_dataset_2003CLP_1900_2024.csv"
fig_dir <- "paper/paper_version2/Figures"

if (!dir.exists(fig_dir)) {
  dir.create(fig_dir, recursive = TRUE)
}

df <- read_csv(csv_path, show_col_types = FALSE)

asset_map <- list(
  ME    = c("ME", "Machinery & Equipment"),
  NRC   = c("NRC", "Non-Residential Construction"),
  RC    = c("RC", "Residential Construction"),
  C     = c("C", "Total Construction"),
  NR    = c("NR", "Total Non-Residential"),
  Total = c("T", "Total Fixed Capital")
)

# Custom Minimalistic Journal Theme (ggplot2)
journal_theme <- theme_minimal(base_family = "sans", base_size = 10) +
  theme(
    panel.background   = element_rect(fill = "white", color = NA),
    plot.background    = element_rect(fill = "white", color = NA),
    panel.grid.major   = element_line(color = "#E5E5E5", linewidth = 0.4),
    panel.grid.minor   = element_blank(),
    panel.border       = element_rect(color = "#CCCCCC", fill = NA, linewidth = 0.6),
    axis.title         = element_text(face = "bold", size = 10),
    axis.text          = element_text(size = 9, color = "#333333"),
    legend.position    = c(0.80, 0.88),
    legend.background  = element_rect(fill = alpha("white", 0.9), color = "#CCCCCC", linewidth = 0.4),
    legend.title       = element_blank(),
    legend.text        = element_text(size = 9),
    plot.margin        = margin(8, 8, 8, 8)
  )

for (asset_code in names(asset_map)) {
  file_code <- asset_map[[asset_code]][1]
  asset_name <- asset_map[[asset_code]][2]

  sub_data <- df %>%
    filter(asset == asset_code, year >= 1901)

  # 1. Depreciation Rate Plot (delta)
  p_delta <- ggplot(sub_data, aes(x = year, y = delta * 100)) +
    geom_hline(yintercept = 0, color = "#888888", linetype = "dashed", linewidth = 0.5) +
    geom_line(color = "#1F77B4", linewidth = 0.9) +
    scale_x_continuous(limits = c(1900, 2025), breaks = seq(1900, 2020, by = 20)) +
    labs(
      x = "Year",
      y = "Annual Rate (%)"
    ) +
    journal_theme

  ggsave(
    filename = file.path(fig_dir, paste0("d_", file_code, "_Kstock_appendix_plot_Drates.png")),
    plot     = p_delta,
    width    = 6.5,
    height   = 3.8,
    dpi      = 300
  )

  # 2. Scrappage / Depletion Rate Plot (z)
  p_z <- ggplot(sub_data, aes(x = year, y = z * 100)) +
    geom_hline(yintercept = 0, color = "#888888", linetype = "dashed", linewidth = 0.5) +
    geom_line(color = "#D62728", linewidth = 0.9) +
    scale_x_continuous(limits = c(1900, 2025), breaks = seq(1900, 2020, by = 20)) +
    labs(
      x = "Year",
      y = "Annual Rate (%)"
    ) +
    journal_theme

  ggsave(
    filename = file.path(fig_dir, paste0("z_", file_code, "_Kstock_appendix_plot_Zrates.png")),
    plot     = p_z,
    width    = 6.5,
    height   = 3.8,
    dpi      = 300
  )
}

cat("Successfully generated 12 journal-standard figures with R / ggplot2.\n")
