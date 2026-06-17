"""
Create a combined panel figure comparing DOS across all three Ge/Sn compositions.
Uses the .dat files output by sumo-dosplot.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

CALCS = [
    {'prefix': 'Ge73Sn143', 'label': 'Ge$_{73}$Sn$_{143}$ (66% Sn)', 'color_Ge': '#e06c75', 'color_Sn': '#61afef'},
    {'prefix': 'Ge43Sn173', 'label': 'Ge$_{43}$Sn$_{173}$ (80% Sn)', 'color_Ge': '#e06c75', 'color_Sn': '#61afef'},
    {'prefix': 'Ge22Sn194', 'label': 'Ge$_{22}$Sn$_{194}$ (90% Sn)', 'color_Ge': '#e06c75', 'color_Sn': '#61afef'},
]

XMIN, XMAX = -6, 4
BASE = os.path.dirname(__file__)


def load_dat(path):
    return np.loadtxt(path, comments='#')


def make_combined_figure():
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)
    fig.suptitle('Density of States — Ge/Sn Alloy Supercells', fontsize=14, fontweight='bold', y=1.02)

    for ax, calc in zip(axes, CALCS):
        prefix = calc['prefix']

        total = load_dat(os.path.join(BASE, f'{prefix}_total_dos.dat'))
        ge    = load_dat(os.path.join(BASE, f'{prefix}_Ge_dos.dat'))
        sn    = load_dat(os.path.join(BASE, f'{prefix}_Sn_dos.dat'))

        energy = total[:, 0]
        mask = (energy >= XMIN) & (energy <= XMAX)

        ax.fill_between(energy[mask], total[mask, 1], alpha=0.15, color='grey', label='Total')
        ax.plot(energy[mask], total[mask, 1], color='grey', lw=1.0)

        ax.fill_between(energy[mask], ge[mask, 1], alpha=0.4, color=calc['color_Ge'], label='Ge')
        ax.plot(energy[mask], ge[mask, 1], color=calc['color_Ge'], lw=1.2)

        ax.fill_between(energy[mask], sn[mask, 1], alpha=0.4, color=calc['color_Sn'], label='Sn')
        ax.plot(energy[mask], sn[mask, 1], color=calc['color_Sn'], lw=1.2)

        ax.axvline(0, color='black', lw=0.8, ls='--', alpha=0.6)
        ax.set_xlim(XMIN, XMAX)
        ax.set_ylim(bottom=0)
        ax.set_xlabel('Energy − $E_{VBM}$ (eV)', fontsize=11)
        ax.set_title(calc['label'], fontsize=11, pad=6)
        ax.legend(fontsize=9, loc='upper right')
        ax.tick_params(axis='both', labelsize=9)

    axes[0].set_ylabel('DOS (states/eV/cell)', fontsize=11)

    plt.tight_layout()
    out_png = os.path.join(BASE, 'dos_combined_panel.png')
    out_svg = os.path.join(BASE, 'dos_combined_panel.svg')
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(out_svg, bbox_inches='tight')
    print(f'Saved {out_png}')
    print(f'Saved {out_svg}')
    plt.close()


def make_overlay_figure():
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_title('Total DOS Overlay — Ge/Sn Alloy Compositions', fontsize=13, fontweight='bold')

    colors = ['#e06c75', '#98c379', '#61afef']
    for calc, color in zip(CALCS, colors):
        prefix = calc['prefix']
        total = load_dat(os.path.join(BASE, f'{prefix}_total_dos.dat'))
        energy = total[:, 0]
        mask = (energy >= XMIN) & (energy <= XMAX)
        ax.plot(energy[mask], total[mask, 1], color=color, lw=1.5, label=calc['label'])
        ax.fill_between(energy[mask], total[mask, 1], alpha=0.12, color=color)

    ax.axvline(0, color='black', lw=0.8, ls='--', alpha=0.6, label='$E_{VBM}$')
    ax.set_xlim(XMIN, XMAX)
    ax.set_ylim(bottom=0)
    ax.set_xlabel('Energy − $E_{VBM}$ (eV)', fontsize=12)
    ax.set_ylabel('DOS (states/eV/cell)', fontsize=12)
    ax.legend(fontsize=10)
    plt.tight_layout()
    out_png = os.path.join(BASE, 'dos_overlay.png')
    out_svg = os.path.join(BASE, 'dos_overlay.svg')
    plt.savefig(out_png, dpi=150, bbox_inches='tight')
    plt.savefig(out_svg, bbox_inches='tight')
    print(f'Saved {out_png}')
    print(f'Saved {out_svg}')
    plt.close()


if __name__ == '__main__':
    make_combined_figure()
    make_overlay_figure()
    print('Done.')
