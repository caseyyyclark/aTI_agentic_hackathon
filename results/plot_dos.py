"""
DOS plotting script for amorphous Ge/Sn/Pb alloy VASP calculations.

Reads DOSCAR files (from .zip archives) and generates:
  - results/dos_individual.png  — 3-panel figure, one DOS per composition
  - results/dos_overlay.png     — all 3 total DOS curves overlaid
  - results/dos_individual.svg  — SVG version
  - results/dos_overlay.svg     — SVG version

Usage:
    pip install matplotlib numpy
    python results/plot_dos.py

From the repository root. The script expects the zip files:
    DOSCAR.zip, 65_DOSCAR.zip, 90_DOSCAR.zip
"""

import zipfile
import io
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "results")
os.makedirs(OUT_DIR, exist_ok=True)

CALCULATIONS = [
    {
        "label": "Ge73Sn143\n(66% Sn)",
        "short": "Ge73Sn143 (66% Sn)",
        "zip": os.path.join(REPO_ROOT, "65_DOSCAR.zip"),
        "efermi": 6.4960,
        "color": "#2196F3",
        "sn_pct": 66.2,
    },
    {
        "label": "Ge43Sn173\n(80% Sn)",
        "short": "Ge43Sn173 (80% Sn)",
        "zip": os.path.join(REPO_ROOT, "DOSCAR.zip"),
        "efermi": 7.0226,
        "color": "#4CAF50",
        "sn_pct": 80.1,
    },
    {
        "label": "Ge22Sn194\n(90% Sn)",
        "short": "Ge22Sn194 (90% Sn)",
        "zip": os.path.join(REPO_ROOT, "90_DOSCAR.zip"),
        "efermi": 7.1099,
        "color": "#F44336",
        "sn_pct": 89.8,
    },
]


def read_doscar_from_zip(zip_path):
    """Extract and return lines from a DOSCAR stored inside a .zip file."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        # Pick the file named DOSCAR (or the only file present)
        target = next((n for n in names if "DOSCAR" in n.upper()), names[0])
        raw = zf.read(target)
    return raw.decode("utf-8", errors="replace").splitlines()


def parse_total_dos(lines):
    """
    Parse the total DOS block from DOSCAR lines.

    DOSCAR format (ISPIN=1):
      Line 0:   NIONS  NKPTS  1  NBLOCK  POTIM
      Lines 1-4: system info
      Line 5:   EMAX  EMIN  EFERMI  WEIGHT  NEDOS
      Lines 6 .. 6+NEDOS-1: energy  dos  integrated

    Returns energies, dos, integrated, efermi.
    """
    header6 = lines[5].split()
    emax = float(header6[0])
    emin = float(header6[1])
    efermi_doscar = float(header6[2])
    nedos = int(header6[4])

    energies = np.empty(nedos)
    dos = np.empty(nedos)
    integrated = np.empty(nedos)

    ncols = len(lines[6].split())
    ispin2 = ncols == 5  # spin-polarized has 5 cols

    for i in range(nedos):
        vals = lines[6 + i].split()
        energies[i] = float(vals[0])
        if ispin2:
            dos[i] = float(vals[1]) + float(vals[2])  # sum spin channels
            integrated[i] = float(vals[3]) + float(vals[4])
        else:
            dos[i] = float(vals[1])
            integrated[i] = float(vals[2])

    return energies, dos, integrated, efermi_doscar


def smooth_dos(energies, dos, sigma_ev=0.05):
    """Apply Gaussian broadening (sigma in eV) to DOS."""
    de = energies[1] - energies[0]
    sigma_pts = sigma_ev / de
    from scipy.ndimage import gaussian_filter1d
    return gaussian_filter1d(dos, sigma_pts)


def load_calc(calc):
    """Load and parse DOS for one calculation."""
    lines = read_doscar_from_zip(calc["zip"])
    energies, dos, integrated, efermi_file = parse_total_dos(lines)
    # Shift to use the Fermi energy extracted from OUTCAR (more reliable)
    energies_shifted = energies - calc["efermi"]
    return energies_shifted, dos, integrated


# ── Try optional smoothing ─────────────────────────────────────────────────────
try:
    from scipy.ndimage import gaussian_filter1d
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ── Load all calculations ──────────────────────────────────────────────────────
print("Loading DOSCAR files…")
data = []
for calc in CALCULATIONS:
    print(f"  Reading {calc['short']} from {os.path.basename(calc['zip'])}")
    en, dos, integ = load_calc(calc)
    data.append((en, dos, integ))
print("Done loading.")


# ── Energy window for plotting ─────────────────────────────────────────────────
E_MIN, E_MAX = -6.0, 4.0   # eV relative to E_F
DOS_WINDOW_MASK = lambda en: (en >= E_MIN) & (en <= E_MAX)


# ══════════════════════════════════════════════════════════════════════════════
# Figure 1 — Individual panels (3 rows)
# ══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
fig.suptitle("Total Density of States — Amorphous Ge/Sn Alloys (PBE)", fontsize=13)

for ax, calc, (en, dos, integ) in zip(axes, CALCULATIONS, data):
    mask = DOS_WINDOW_MASK(en)
    dos_plot = dos.copy()
    if HAS_SCIPY:
        dos_plot = gaussian_filter1d(dos_plot, 1.0)

    ax.fill_between(en[mask], dos_plot[mask], alpha=0.4, color=calc["color"])
    ax.plot(en[mask], dos_plot[mask], color=calc["color"], lw=1.2)
    ax.axvline(0, color="k", lw=0.8, ls="--", alpha=0.7, label="$E_F$")
    ax.set_ylabel("DOS (states/eV)", fontsize=9)
    ax.set_title(calc["short"], fontsize=10, pad=3)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_xlim(E_MIN, E_MAX)
    ymax = dos_plot[mask].max() * 1.12
    ax.set_ylim(0, ymax)
    ax.tick_params(labelsize=8)

    # annotate Sn%
    ax.text(0.98, 0.92, f"Sn = {calc['sn_pct']:.1f}%",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

axes[-1].set_xlabel("$E - E_F$ (eV)", fontsize=10)

plt.tight_layout()
for ext in ("png", "svg"):
    path = os.path.join(OUT_DIR, f"dos_individual.{ext}")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"Saved {path}")
plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# Figure 2 — Overlay of all compositions
# ══════════════════════════════════════════════════════════════════════════════
fig2, ax2 = plt.subplots(figsize=(8, 5))
fig2.suptitle("Total DOS — All Compositions (PBE, aligned to $E_F$)", fontsize=13)

for calc, (en, dos, integ) in zip(CALCULATIONS, data):
    mask = DOS_WINDOW_MASK(en)
    dos_plot = dos.copy()
    if HAS_SCIPY:
        dos_plot = gaussian_filter1d(dos_plot, 1.0)
    ax2.plot(en[mask], dos_plot[mask], color=calc["color"], lw=1.5,
             label=calc["short"])

ax2.axvline(0, color="k", lw=0.9, ls="--", alpha=0.7, label="$E_F$")
ax2.set_xlabel("$E - E_F$ (eV)", fontsize=11)
ax2.set_ylabel("DOS (states/eV)", fontsize=11)
ax2.legend(fontsize=9)
ax2.set_xlim(E_MIN, E_MAX)
ax2.set_ylim(bottom=0)
ax2.tick_params(labelsize=9)

plt.tight_layout()
for ext in ("png", "svg"):
    path = os.path.join(OUT_DIR, f"dos_overlay.{ext}")
    fig2.savefig(path, dpi=150, bbox_inches="tight")
    print(f"Saved {path}")
plt.close(fig2)


# ══════════════════════════════════════════════════════════════════════════════
# Figure 3 — Gap zoom
# ══════════════════════════════════════════════════════════════════════════════
E_MIN_GAP, E_MAX_GAP = -1.5, 1.5

fig3, axes3 = plt.subplots(1, 3, figsize=(12, 4), sharey=False)
fig3.suptitle("DOS near Band Gap — Amorphous Ge/Sn Alloys", fontsize=13)

for ax, calc, (en, dos, integ) in zip(axes3, CALCULATIONS, data):
    mask = (en >= E_MIN_GAP) & (en <= E_MAX_GAP)
    dos_plot = dos.copy()
    if HAS_SCIPY:
        dos_plot = gaussian_filter1d(dos_plot, 0.5)

    ax.fill_between(en[mask], dos_plot[mask], alpha=0.4, color=calc["color"])
    ax.plot(en[mask], dos_plot[mask], color=calc["color"], lw=1.2)
    ax.axvline(0, color="k", lw=0.8, ls="--", alpha=0.7)
    ax.set_xlabel("$E - E_F$ (eV)", fontsize=9)
    ax.set_ylabel("DOS (states/eV)", fontsize=9)
    ax.set_title(calc["short"], fontsize=9, pad=3)
    ax.set_xlim(E_MIN_GAP, E_MAX_GAP)
    ax.set_ylim(bottom=0)
    ax.tick_params(labelsize=8)

plt.tight_layout()
for ext in ("png", "svg"):
    path = os.path.join(OUT_DIR, f"dos_gap_zoom.{ext}")
    fig3.savefig(path, dpi=150, bbox_inches="tight")
    print(f"Saved {path}")
plt.close(fig3)

print("\nAll DOS plots written to results/")
print("Files: dos_individual.png/svg, dos_overlay.png/svg, dos_gap_zoom.png/svg")
