"""Parse VASP calculation outputs for Ge/Sn alloy supercells."""
import re
import os
import sys
import math
import zipfile
import numpy as np
import csv
import json

REPO = "/home/runner/work/aTI_agentic_hackathon/aTI_agentic_hackathon"

calcs = {
    "Ge43Sn173_80pctSn": {
        "prefix": "",
        "poscar": "POSCAR",
        "outcar": "OUTCAR",
        "eigenval": "EIGENVAL",
        "doscar_zip": "DOSCAR.zip",
        "vasprun_zip": "vasprun.xml.zip",
        "n_Ge": 43, "n_Sn": 173, "n_Pb": 0,
    },
    "Ge73Sn143_66pctSn": {
        "prefix": "65_",
        "poscar": "65_POSCAR",
        "outcar": "65_OUTCAR",
        "eigenval": "65_EIGENVAL",
        "doscar_zip": "65_DOSCAR.zip",
        "vasprun_zip": "65_vasprun.xml.zip",
        "n_Ge": 73, "n_Sn": 143, "n_Pb": 0,
    },
    "Ge22Sn194_90pctSn": {
        "prefix": "90_",
        "poscar": "90_POSCAR",
        "outcar": "90_OUTCAR",
        "eigenval": "90_EIGENVAL",
        "doscar_zip": "90_DOSCAR.zip",
        "vasprun_zip": "90_vasprun.xml.zip",
        "n_Ge": 22, "n_Sn": 194, "n_Pb": 0,
    },
}

def parse_outcar(path):
    """Extract key quantities from OUTCAR."""
    with open(path) as f:
        content = f.read()

    result = {}

    # Final total energy (last TOTEN)
    toten_matches = re.findall(r"free energy\s+TOTEN\s+=\s+([-\d.]+)\s+eV", content)
    result["total_energy_eV"] = float(toten_matches[-1]) if toten_matches else None

    # Energy without entropy (sigma->0)
    sig0_matches = re.findall(r"energy\(sigma->0\)\s+=\s+([-\d.]+)", content)
    result["energy_sigma0_eV"] = float(sig0_matches[-1]) if sig0_matches else None

    # Convergence
    if "aborting loop because EDIFF is reached" in content:
        result["converged"] = True
        result["convergence_note"] = "EDIFF reached"
    else:
        result["converged"] = False
        result["convergence_note"] = "EDIFF NOT reached (possible NELM exhaustion)"

    # E-fermi
    efermi_matches = re.findall(r"E-fermi\s*:\s*([-\d.]+)", content)
    result["E_fermi_eV"] = float(efermi_matches[-1]) if efermi_matches else None

    # NELM
    nelm_match = re.search(r"NELM\s*=\s*(\d+)", content)
    result["NELM"] = int(nelm_match.group(1)) if nelm_match else None

    # NSW
    nsw_match = re.search(r"NSW\s*=\s*(\d+)", content)
    result["NSW"] = int(nsw_match.group(1)) if nsw_match else None

    # Volume
    vol_matches = re.findall(r"volume of cell\s*:\s*([\d.]+)", content)
    result["volume_A3"] = float(vol_matches[-1]) if vol_matches else None

    # Final lattice vectors (last occurrence)
    lat_pattern = r"direct lattice vectors\s+reciprocal lattice vectors\s+([-\d. ]+)\n([-\d. ]+)\n([-\d. ]+)"
    lat_matches = re.findall(lat_pattern, content)
    if lat_matches:
        rows = lat_matches[-1]
        vecs = []
        for row in rows:
            vals = row.split()
            vecs.append([float(v) for v in vals[:3]])
        result["lattice_matrix"] = vecs
        # Compute a, b, c, alpha, beta, gamma
        a = np.linalg.norm(vecs[0])
        b = np.linalg.norm(vecs[1])
        c = np.linalg.norm(vecs[2])
        v0, v1, v2 = np.array(vecs[0]), np.array(vecs[1]), np.array(vecs[2])
        alpha = math.degrees(math.acos(np.dot(v1, v2) / (b * c)))
        beta  = math.degrees(math.acos(np.dot(v0, v2) / (a * c)))
        gamma = math.degrees(math.acos(np.dot(v0, v1) / (a * b)))
        result["a_A"] = round(a, 4)
        result["b_A"] = round(b, 4)
        result["c_A"] = round(c, 4)
        result["alpha_deg"] = round(alpha, 3)
        result["beta_deg"]  = round(beta, 3)
        result["gamma_deg"] = round(gamma, 3)
    else:
        result["a_A"] = result["b_A"] = result["c_A"] = None
        result["alpha_deg"] = result["beta_deg"] = result["gamma_deg"] = None

    # Warnings
    warnings = []
    if "Sub-Space-Matrix is not hermitian in DAV" in content:
        warnings.append("Sub-Space-Matrix not hermitian")
    if "WARNING: Sub-Space" in content:
        warnings.append("Sub-Space warning")
    if "WARNING" in content:
        warn_lines = [l.strip() for l in content.split("\n") if "WARNING" in l]
        warnings.extend(warn_lines[:5])
    if "BRMIX" in content and "BRMIX: very serious problem" in content:
        warnings.append("BRMIX serious problem")
    result["warnings"] = list(set(warnings))[:10]

    return result


def parse_eigenval(path, E_fermi):
    """Estimate band gap from EIGENVAL file."""
    with open(path) as f:
        lines = f.readlines()

    # Header: line 6 has NKPTS, NBANDS, NIONS-ish
    try:
        header = lines[5].split()
        nkpts = int(header[1])
        nbands = int(header[2])
    except Exception:
        return {"band_gap_eV": None, "band_gap_note": "parse error"}

    # Parse eigenvalues: find VBM and CBM
    vbm = -1e10
    cbm =  1e10

    line_idx = 7  # Skip header block (line 0-5 = 6 header lines, line 6 blank, then kpoints)
    for k in range(nkpts):
        line_idx += 1  # blank line before k-point
        line_idx += 1  # k-point line
        for b in range(nbands):
            if line_idx >= len(lines):
                break
            parts = lines[line_idx].split()
            line_idx += 1
            if len(parts) >= 3:
                energy = float(parts[1])
                occ = float(parts[2])
                if occ > 0.5:  # occupied
                    if energy > vbm:
                        vbm = energy
                else:  # unoccupied
                    if energy < cbm:
                        cbm = energy

    if vbm == -1e10 or cbm == 1e10:
        return {"band_gap_eV": None, "VBM_eV": None, "CBM_eV": None, "band_gap_note": "could not determine"}

    gap = cbm - vbm
    result = {
        "VBM_eV": round(vbm, 4),
        "CBM_eV": round(cbm, 4),
        "band_gap_eV": round(max(gap, 0.0), 4),
    }
    if gap < 0:
        result["band_gap_note"] = f"metallic (VBM > CBM by {-gap:.3f} eV)"
    else:
        result["band_gap_note"] = f"semiconductor (gap = {gap:.3f} eV)"
    return result


# Run parsing
results = {}
for name, calc in calcs.items():
    print(f"\n=== Processing {name} ===")
    n_atoms = calc["n_Ge"] + calc["n_Sn"] + calc["n_Pb"]
    sn_frac = calc["n_Sn"] / n_atoms
    ge_frac = calc["n_Ge"] / n_atoms

    outcar_path = os.path.join(REPO, calc["outcar"])
    eigenval_path = os.path.join(REPO, calc["eigenval"])

    outcar_data = parse_outcar(outcar_path)
    print(f"  Converged: {outcar_data['converged']} ({outcar_data['convergence_note']})")
    print(f"  Total energy: {outcar_data['total_energy_eV']} eV")
    print(f"  E-fermi: {outcar_data['E_fermi_eV']} eV")
    print(f"  Volume: {outcar_data['volume_A3']} A^3")
    print(f"  a={outcar_data['a_A']}, b={outcar_data['b_A']}, c={outcar_data['c_A']}")

    eigenval_data = parse_eigenval(eigenval_path, outcar_data["E_fermi_eV"])
    print(f"  Band gap: {eigenval_data.get('band_gap_eV')} eV ({eigenval_data.get('band_gap_note')})")
    print(f"  Warnings: {outcar_data['warnings']}")

    results[name] = {
        "name": name,
        "n_Ge": calc["n_Ge"],
        "n_Sn": calc["n_Sn"],
        "n_Pb": calc["n_Pb"],
        "n_atoms": n_atoms,
        "Sn_fraction": round(sn_frac, 4),
        "Ge_fraction": round(ge_frac, 4),
        "formula": f"Ge{calc['n_Ge']}Sn{calc['n_Sn']}",
        **outcar_data,
        **eigenval_data,
    }
    if outcar_data["total_energy_eV"] is not None:
        results[name]["energy_per_atom_eV"] = round(outcar_data["total_energy_eV"] / n_atoms, 6)
    else:
        results[name]["energy_per_atom_eV"] = None

# Save JSON for later use
with open(os.path.join(REPO, "parsed_results.json"), "w") as f:
    json.dump(results, f, indent=2, default=str)
print("\nSaved parsed_results.json")
