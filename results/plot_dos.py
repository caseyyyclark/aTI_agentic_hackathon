"""
DOS plotter for Ge/Sn/Pb alloy VASP calculations.
Reads DOSCAR directly from .zip archives using Python's built-in zipfile module.
Generates three figures:
  dos_individual.{png,svg}  - 3-panel subplot, one DOS per composition
  dos_overlay.{png,svg}     - all compositions overlaid on one axis
  dos_gap_zoom.{png,svg}    - gap region zoomed to ±1.5 eV around E_F
"""

import zipfile
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CALCULATIONS = [
    {
        "label": "Ge₄₃Sn₁₇₃ (80% Sn)",
        "zip":   os.path.join(REPO, "DOSCAR.zip"),
        "color": "#1f77b4",
        "sn_pct": 80.1,
    },
    {
        "label": "Ge₇₃Sn₁₄₃ (66% Sn)",
        "zip":   os.path.join(REPO, "65_DOSCAR.zip"),
        "color": "#ff7f0e",
        "sn_pct": 66.2,
    },
    {
        "label": "Ge₂₂Sn₁₉₄ (90% Sn)",
        "zip":   os.path.join(REPO, "90_DOSCAR.zip"),
        "color": "#2ca02c",
        "sn_pct": 89.8,
    },
]

RESULTS = os.path.join(REPO, "results")
os.makedirs(RESULTS, exist_ok=True)


def read_doscar(zip_path):
    """
    Parse total DOS from a DOSCAR.zip.

    Returns
    -------
    energies : ndarray  shape (NEDOS,)
    dos      : ndarray  shape (NEDOS,)
    efermi   : float
    """
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        # Find the DOSCAR entry (may be called DOSCAR, 65_DOSCAR, etc.)
        doscar_name = next(
            (n for n in names if os.path.basename(n).upper() == "DOSCAR"
             or os.path.basename(n).endswith("DOSCAR")),
            names[0],
        )
        with zf.open(doscar_name) as fh:
            lines = fh.read().decode("utf-8").splitlines()

    # Line 0: NIONS NKDIV ISPIN NBLOCK NION
    header0 = lines[0].split()
    ispin = int(header0[2])

    # Line 5: EMAX  EMIN  EFERMI  WEIGHT  (sometimes a 5th token = NEDOS)
    header5 = lines[5].split()
    efermi = float(header5[2])

    # Determine NEDOS: count consecutive data lines starting at line 6
    # Data lines for total DOS have 3 cols (ISPIN=1) or 5 cols (ISPIN=2)
    n_data_cols = 3 + 2 * (ispin - 1)  # 3 or 5

    energies, dos = [], []
    for line in lines[6:]:
        parts = line.split()
        if len(parts) != n_data_cols:
            break  # hit an ion-block header
        e = float(parts[0])
        d = float(parts[1])
        energies.append(e)
        dos.append(d)

    return np.array(energies), np.array(dos), efermi


def smooth(y, sigma=2.0):
    """Simple Gaussian smoothing via convolution (no scipy needed)."""
    kernel_size = max(1, int(6 * sigma))
    if kernel_size % 2 == 0:
        kernel_size += 1
    x = np.arange(kernel_size) - kernel_size // 2
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= kernel.sum()
    return np.convolve(y, kernel, mode="same")


def set_axes_style(ax):
    ax.set_xlabel("E − E$_F$ (eV)", fontsize=11)
    ax.set_ylabel("DOS (states/eV)", fontsize=11)
    ax.axvline(0, color="gray", lw=0.8, ls="--", alpha=0.7)
    ax.axhline(0, color="gray", lw=0.5, alpha=0.5)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.tick_params(which="both", direction="in", top=True, right=True)


# ── Load all data ──────────────────────────────────────────────────────────────
datasets = []
for calc in CALCULATIONS:
    print(f"Reading {calc['zip']} …")
    energies, dos, efermi = read_doscar(calc["zip"])
    energies_shifted = energies - efermi
    dos_smoothed = smooth(dos, sigma=1.5)
    datasets.append({
        **calc,
        "energies": energies_shifted,
        "dos_raw":  dos,
        "dos":      dos_smoothed,
        "efermi":   efermi,
    })
    print(f"  E_F = {efermi:.4f} eV,  NEDOS = {len(energies)}")

# ── Plot 1: Individual panels ──────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
fig.suptitle("Total DOS — Amorphous Ge/Sn Alloys", fontsize=13, y=0.98)

for ax, d in zip(axes, datasets):
    mask = (d["energies"] >= -6) & (d["energies"] <= 6)
    ax.fill_between(d["energies"][mask], d["dos"][mask],
                    alpha=0.35, color=d["color"])
    ax.plot(d["energies"][mask], d["dos"][mask],
            color=d["color"], lw=1.2, label=d["label"])
    ax.legend(loc="upper left", fontsize=9)
    set_axes_style(ax)
    ymax = d["dos"][mask].max()
    ax.set_ylim(bottom=-ymax * 0.05)

axes[-1].set_xlim(-6, 6)
plt.tight_layout(rect=[0, 0, 1, 0.97])
for ext in ("png", "svg"):
    fig.savefig(os.path.join(RESULTS, f"dos_individual.{ext}"),
                dpi=200, bbox_inches="tight")
print("Saved dos_individual.png / .svg")
plt.close(fig)

# ── Plot 2: Overlay ────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
fig.suptitle("Total DOS Overlay — Amorphous Ge/Sn Alloys", fontsize=13)

for d in datasets:
    mask = (d["energies"] >= -6) & (d["energies"] <= 6)
    ax.plot(d["energies"][mask], d["dos"][mask],
            color=d["color"], lw=1.4, label=d["label"])

set_axes_style(ax)
ax.set_xlim(-6, 6)
ax.legend(fontsize=10)
ax.set_title("")
plt.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(os.path.join(RESULTS, f"dos_overlay.{ext}"),
                dpi=200, bbox_inches="tight")
print("Saved dos_overlay.png / .svg")
plt.close(fig)

# ── Plot 3: Gap region zoom ────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
fig.suptitle("DOS near E$_F$ — Gap Region", fontsize=13)

for d in datasets:
    mask = (d["energies"] >= -1.5) & (d["energies"] <= 1.5)
    ax.fill_between(d["energies"][mask], d["dos"][mask],
                    alpha=0.25, color=d["color"])
    ax.plot(d["energies"][mask], d["dos"][mask],
            color=d["color"], lw=1.4, label=d["label"])

set_axes_style(ax)
ax.set_xlim(-1.5, 1.5)
ax.legend(fontsize=10)
plt.tight_layout()
for ext in ("png", "svg"):
    fig.savefig(os.path.join(RESULTS, f"dos_gap_zoom.{ext}"),
                dpi=200, bbox_inches="tight")
print("Saved dos_gap_zoom.png / .svg")
plt.close(fig)

print("\nAll DOS plots written to results/")
