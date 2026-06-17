"""
Generate composition plots for Ge/Sn amorphous alloy DFT data.

Usage:
    pip install matplotlib numpy
    python results/plot_composition.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Data extracted from OUTCAR/EIGENVAL files
data = [
    {
        "label": "Ge73Sn143\n(66% Sn)",
        "formula": "Ge73Sn143",
        "Sn_pct": 66.2,
        "Ge_pct": 33.8,
        "total_energy_eV": -991.06520346,
        "energy_per_atom_eV": -4.58826,
        "band_gap_eV": 0.1962,
        "volume_A3": 5789.14,
        "volume_per_atom_A3": 26.80,
        "lattice_a": 17.943,
        "lattice_b": 17.945,
        "lattice_c": 17.987,
    },
    {
        "label": "Ge43Sn173\n(80% Sn)",
        "formula": "Ge43Sn173",
        "Sn_pct": 80.1,
        "Ge_pct": 19.9,
        "total_energy_eV": -976.22275457,
        "energy_per_atom_eV": -4.52011,
        "band_gap_eV": 0.2323,
        "volume_A3": 5856.63,
        "volume_per_atom_A3": 27.11,
        "lattice_a": 18.102,
        "lattice_b": 17.955,
        "lattice_c": 18.022,
    },
    {
        "label": "Ge22Sn194\n(90% Sn)",
        "formula": "Ge22Sn194",
        "Sn_pct": 89.8,
        "Ge_pct": 10.2,
        "total_energy_eV": -962.71688806,
        "energy_per_atom_eV": -4.45702,
        "band_gap_eV": 0.2337,
        "volume_A3": 6037.84,
        "volume_per_atom_A3": 27.95,
        "lattice_a": 18.212,
        "lattice_b": 18.186,
        "lattice_c": 18.234,
    },
]

sn_pcts = [d["Sn_pct"] for d in data]
energies = [d["energy_per_atom_eV"] for d in data]
gaps = [d["band_gap_eV"] for d in data]
vols = [d["volume_per_atom_A3"] for d in data]
labels = [d["formula"] for d in data]
a_params = [d["lattice_a"] for d in data]
b_params = [d["lattice_b"] for d in data]
c_params = [d["lattice_c"] for d in data]

colors = ["#2196F3", "#FF5722", "#4CAF50"]
markers = ["o", "s", "^"]

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle("Amorphous GeSn Alloys: DFT Property Trends\n(VASP PBE, 216-atom supercells, Γ-only)",
             fontsize=13, fontweight="bold")

# Panel 1: Energy per atom vs Sn%
ax = axes[0, 0]
for i, d in enumerate(data):
    ax.scatter(d["Sn_pct"], d["energy_per_atom_eV"], color=colors[i],
               marker=markers[i], s=120, zorder=5, label=d["formula"])
ax.plot(sn_pcts, energies, "k--", alpha=0.4, zorder=1)
ax.set_xlabel("Sn fraction (%)")
ax.set_ylabel("Energy per atom (eV)")
ax.set_title("Energy per atom vs Composition")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
for i, (x, y, lbl) in enumerate(zip(sn_pcts, energies, labels)):
    ax.annotate(f"{y:.3f}", (x, y), textcoords="offset points",
                xytext=(8, 3), fontsize=8, color=colors[i])

# Panel 2: Band gap vs Sn%
ax = axes[0, 1]
for i, d in enumerate(data):
    ax.scatter(d["Sn_pct"], d["band_gap_eV"], color=colors[i],
               marker=markers[i], s=120, zorder=5, label=d["formula"])
ax.plot(sn_pcts, gaps, "k--", alpha=0.4, zorder=1)
ax.set_xlabel("Sn fraction (%)")
ax.set_ylabel("Band gap (eV)")
ax.set_title("Band Gap vs Composition\n(Γ-only, SIGMA=0.05 eV — indicative only)")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
ax.set_ylim(bottom=0)
for i, (x, y, lbl) in enumerate(zip(sn_pcts, gaps, labels)):
    ax.annotate(f"{y:.3f} eV", (x, y), textcoords="offset points",
                xytext=(8, 3), fontsize=8, color=colors[i])

# Panel 3: Volume per atom vs Sn%
ax = axes[1, 0]
for i, d in enumerate(data):
    ax.scatter(d["Sn_pct"], d["volume_per_atom_A3"], color=colors[i],
               marker=markers[i], s=120, zorder=5, label=d["formula"])
ax.plot(sn_pcts, vols, "k--", alpha=0.4, zorder=1)
ax.set_xlabel("Sn fraction (%)")
ax.set_ylabel("Volume per atom (Å³)")
ax.set_title("Volume per atom vs Composition")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Panel 4: Lattice parameters vs Sn%
ax = axes[1, 1]
ax.plot(sn_pcts, a_params, "o-", color="#E91E63", label="a", linewidth=1.5, markersize=8)
ax.plot(sn_pcts, b_params, "s-", color="#9C27B0", label="b", linewidth=1.5, markersize=8)
ax.plot(sn_pcts, c_params, "^-", color="#FF9800", label="c", linewidth=1.5, markersize=8)
ax.set_xlabel("Sn fraction (%)")
ax.set_ylabel("Lattice parameter (Å)")
ax.set_title("Lattice Parameters vs Composition")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
out_path = os.path.join(OUT_DIR, "composition_plots.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path}")
plt.close()

# --- Separate band gap plot ---
fig, ax = plt.subplots(figsize=(7, 5))
for i, d in enumerate(data):
    ax.bar(d["Sn_pct"], d["band_gap_eV"], width=6,
           color=colors[i], alpha=0.8, label=d["formula"],
           edgecolor="k", linewidth=0.8)
    ax.text(d["Sn_pct"], d["band_gap_eV"] + 0.003,
            f"{d['band_gap_eV']:.3f} eV", ha="center", va="bottom", fontsize=10)

ax.set_xlabel("Sn fraction (%)", fontsize=12)
ax.set_ylabel("Band gap (eV)", fontsize=12)
ax.set_title("Band Gap vs Sn Composition\nAmorphous Ge$_{1-x}$Sn$_x$ (PBE, Γ-only)", fontsize=12)
ax.legend(fontsize=10)
ax.set_ylim(0, max(gaps) * 1.25)
ax.grid(axis="y", alpha=0.3)
ax.set_xticks(sn_pcts)
ax.set_xticklabels([f"{x:.1f}%" for x in sn_pcts])
out_path2 = os.path.join(OUT_DIR, "bandgap_vs_composition.png")
plt.savefig(out_path2, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path2}")
plt.close()

# --- Energy per atom plot ---
fig, ax = plt.subplots(figsize=(7, 5))
ref_e = min(energies)
formation_energies = [e - ref_e for e in energies]
ax2 = ax.twinx()
ax.plot(sn_pcts, energies, "ko-", markersize=10, linewidth=2, label="E/atom (eV)")
for i, (x, y) in enumerate(zip(sn_pcts, energies)):
    ax.scatter(x, y, color=colors[i], s=150, zorder=5)
    ax.annotate(f"{y:.4f}", (x, y), textcoords="offset points",
                xytext=(8, 4), fontsize=9)
ax.set_xlabel("Sn fraction (%)", fontsize=12)
ax.set_ylabel("Energy per atom (eV/atom)", fontsize=12)
ax.set_title("Energy per Atom vs Sn Composition\nAmorphous Ge$_{1-x}$Sn$_x$ (PBE, 216 atoms)", fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_xticks(sn_pcts)
ax.set_xticklabels([f"{x:.1f}% Sn" for x in sn_pcts])
out_path3 = os.path.join(OUT_DIR, "energy_vs_composition.png")
plt.savefig(out_path3, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path3}")
plt.close()

print("All plots generated successfully.")
