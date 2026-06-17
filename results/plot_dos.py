"""
Plot total DOS for three amorphous Ge/Sn alloy supercells from DOSCAR.zip files.
Generates individual, overlay, and gap-zoom figures in both PNG and SVG formats.
"""

import zipfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

try:
    from scipy.ndimage import gaussian_filter1d
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

REPO = Path(__file__).parent.parent

CALCS = [
    {
        "label": "Ge73Sn143 (66% Sn)",
        "doscar_zip": REPO / "65_DOSCAR.zip",
        "efermi": 6.4960,
        "color": "#2196F3",
        "linestyle": "-",
    },
    {
        "label": "Ge43Sn173 (80% Sn)",
        "doscar_zip": REPO / "DOSCAR.zip",
        "efermi": 7.0226,
        "color": "#FF9800",
        "linestyle": "--",
    },
    {
        "label": "Ge22Sn194 (90% Sn)",
        "doscar_zip": REPO / "90_DOSCAR.zip",
        "efermi": 7.1099,
        "color": "#4CAF50",
        "linestyle": "-.",
    },
]

SIGMA = 2  # smoothing width in grid points (mild)


def read_total_dos(doscar_zip: Path):
    """Return (energy, dos) arrays from a DOSCAR.zip file."""
    with zipfile.ZipFile(doscar_zip) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            lines = fh.readlines()

    # Line index 5 (6th line): EMAX EMIN NEDOS EFERMI WEIGHT
    header = lines[5].decode().split()
    nedos = int(header[2])

    energies = np.empty(nedos)
    dos = np.empty(nedos)
    for i, line in enumerate(lines[6 : 6 + nedos]):
        parts = line.decode().split()
        energies[i] = float(parts[0])
        dos[i] = float(parts[1])  # total DOS (ISPIN=1 → only one DOS column)

    return energies, dos


def smooth(dos):
    if HAS_SCIPY and SIGMA > 0:
        return gaussian_filter1d(dos, sigma=SIGMA)
    return dos


def plot_individual(calcs, out_dir: Path):
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=False)
    fig.suptitle("Total DOS — Amorphous Ge/Sn Alloys", fontsize=13, fontweight="bold")

    for ax, calc in zip(axes, calcs):
        energies, dos = read_total_dos(calc["doscar_zip"])
        e_shifted = energies - calc["efermi"]
        dos_sm = smooth(dos)

        ax.fill_between(e_shifted, dos_sm, alpha=0.25, color=calc["color"])
        ax.plot(e_shifted, dos_sm, color=calc["color"], lw=1.4, label=calc["label"])
        ax.axvline(0, color="k", lw=0.8, ls=":")
        ax.set_xlim(-10, 8)
        ax.set_ylim(bottom=0)
        ax.set_ylabel("DOS (states/eV)", fontsize=9)
        ax.legend(loc="upper left", fontsize=9)
        ax.tick_params(labelsize=8)

    axes[-1].set_xlabel("Energy − E$_F$ (eV)", fontsize=10)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"dos_individual.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved dos_individual.png / .svg")


def plot_overlay(calcs, out_dir: Path):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_title("Total DOS Overlay — Amorphous Ge/Sn Alloys", fontsize=12, fontweight="bold")

    for calc in calcs:
        energies, dos = read_total_dos(calc["doscar_zip"])
        e_shifted = energies - calc["efermi"]
        dos_sm = smooth(dos)
        ax.plot(e_shifted, dos_sm, color=calc["color"], lw=1.5,
                ls=calc["linestyle"], label=calc["label"])

    ax.axvline(0, color="k", lw=0.9, ls=":", label="$E_F$")
    ax.set_xlim(-10, 8)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Energy − E$_F$ (eV)", fontsize=11)
    ax.set_ylabel("DOS (states/eV)", fontsize=11)
    ax.legend(fontsize=10)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"dos_overlay.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved dos_overlay.png / .svg")


def plot_gap_zoom(calcs, out_dir: Path):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.set_title("DOS Near Band Gap — Ge/Sn Alloys", fontsize=12, fontweight="bold")

    for calc in calcs:
        energies, dos = read_total_dos(calc["doscar_zip"])
        e_shifted = energies - calc["efermi"]
        dos_sm = smooth(dos)
        ax.plot(e_shifted, dos_sm, color=calc["color"], lw=1.6,
                ls=calc["linestyle"], label=calc["label"])

    ax.axvline(0, color="k", lw=0.9, ls=":", label="$E_F$")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Energy − E$_F$ (eV)", fontsize=11)
    ax.set_ylabel("DOS (states/eV)", fontsize=11)
    ax.legend(fontsize=10)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(out_dir / f"dos_gap_zoom.{ext}", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved dos_gap_zoom.png / .svg")


if __name__ == "__main__":
    out_dir = Path(__file__).parent
    out_dir.mkdir(exist_ok=True)

    print(f"scipy smoothing: {'enabled' if HAS_SCIPY else 'disabled'}")
    print("Reading DOSCARs...")

    plot_individual(CALCS, out_dir)
    plot_overlay(CALCS, out_dir)
    plot_gap_zoom(CALCS, out_dir)

    print("\nDone. Files written to results/:")
    for f in sorted(out_dir.glob("dos_*.png")) + sorted(out_dir.glob("dos_*.svg")):
        print(f"  {f.name}")
