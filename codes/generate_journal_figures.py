import pandas as pd
import matplotlib.pyplot as plt
import os

# Set working directory to repo root
csv_path = 'outputs/HARMONIZED_BCCH_2003CLP_v1/harmonized_master_dataset_2003CLP_1900_2024.csv'
fig_dir = 'paper/paper_version2/Figures'
os.makedirs(fig_dir, exist_ok=True)

df = pd.read_csv(csv_path)

# Minimalistic ggplot-inspired journal theme setup
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.edgecolor': '#cccccc',
    'axes.linewidth': 0.8,
    'axes.facecolor': '#ffffff',
    'figure.facecolor': '#ffffff',
    'grid.color': '#e5e5e5',
    'grid.linestyle': ':',
    'grid.linewidth': 0.7,
    'legend.frameon': True,
    'legend.framealpha': 0.9,
    'legend.edgecolor': '#cccccc',
    'legend.fontsize': 9,
})

asset_map = {
    'ME': ('ME', 'Machinery & Equipment'),
    'NRC': ('NRC', 'Non-Residential Construction'),
    'RC': ('RC', 'Residential Construction'),
    'C': ('C', 'Total Construction'),
    'NR': ('NR', 'Total Non-Residential'),
    'Total': ('T', 'Total Fixed Capital')
}

for asset_code, (file_code, asset_name) in asset_map.items():
    sub = df[df['asset'] == asset_code].sort_values('year')
    sub_rates = sub[sub['year'] >= 1901]

    # 1. Depreciation Rate Plot (delta) - NO internal title, subtitle, or notes
    fig, ax = plt.subplots(figsize=(7, 3.8), dpi=300)
    ax.plot(sub_rates['year'], sub_rates['delta'] * 100, color='#1f77b4', lw=1.8, label=r'Implicit Net Depreciation Rate ($\delta_t$)')
    ax.axhline(0, color='#888888', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.set_xlabel('Year', fontsize=10, labelpad=5)
    ax.set_ylabel('Annual Rate (%)', fontsize=10, labelpad=5)
    ax.set_xlim(1900, 2025)
    ax.grid(True)
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f'd_{file_code}_Kstock_appendix_plot_Drates.png'), bbox_inches='tight')
    plt.close()

    # 2. Scrappage / Depletion Rate Plot (z) - NO internal title, subtitle, or notes
    fig, ax = plt.subplots(figsize=(7, 3.8), dpi=300)
    ax.plot(sub_rates['year'], sub_rates['z'] * 100, color='#d62728', lw=1.8, label=r'Implicit Gross Depletion Rate ($z_t$)')
    ax.axhline(0, color='#888888', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.set_xlabel('Year', fontsize=10, labelpad=5)
    ax.set_ylabel('Annual Rate (%)', fontsize=10, labelpad=5)
    ax.set_xlim(1900, 2025)
    ax.grid(True)
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, f'z_{file_code}_Kstock_appendix_plot_Zrates.png'), bbox_inches='tight')
    plt.close()

print('Successfully generated journal-standard figures with figure protocol (titles/notes excluded from plot canvas).')
