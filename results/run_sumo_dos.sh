#!/usr/bin/env bash
# Generate DOS plots using sumo for all three Ge/Sn alloy calculations.
# Prerequisites: pip install sumo matplotlib
# Run from the repo root directory.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${REPO_DIR}/results"
mkdir -p "${OUT_DIR}"

# ---- Helper: unzip DOSCAR and vasprun.xml if needed ----
unzip_if_needed() {
    local zipfile="$1"
    local outfile="$2"
    if [ ! -f "${outfile}" ]; then
        echo "Extracting ${zipfile}..."
        unzip -o "${zipfile}" -d "${REPO_DIR}"
    else
        echo "${outfile} already exists, skipping unzip."
    fi
}

# ---- Calculation 1: Ge43Sn173 (~80% Sn) ----
echo "=== Processing Ge43Sn173 (80% Sn) ==="
unzip_if_needed "${REPO_DIR}/vasprun.xml.zip"   "${REPO_DIR}/vasprun.xml"
unzip_if_needed "${REPO_DIR}/DOSCAR.zip"         "${REPO_DIR}/DOSCAR"

cd "${REPO_DIR}"
sumo-dosplot \
    --code vasp \
    --filenames vasprun.xml \
    --output "${OUT_DIR}/dos_Ge43Sn173_80pctSn.png" \
    --no-legend \
    --width 6 --height 4 \
    --xmin -10 --xmax 5 \
    --title "DOS: Ge43Sn173 (80% Sn, amorphous)" \
    || echo "WARNING: sumo-dosplot failed for root calculation"

# ---- Calculation 2: Ge73Sn143 (~66% Sn) ----
echo ""
echo "=== Processing Ge73Sn143 (66% Sn) ==="
unzip_if_needed "${REPO_DIR}/65_vasprun.xml.zip" "${REPO_DIR}/65_vasprun.xml"
unzip_if_needed "${REPO_DIR}/65_DOSCAR.zip"       "${REPO_DIR}/65_DOSCAR"

sumo-dosplot \
    --code vasp \
    --filenames 65_vasprun.xml \
    --output "${OUT_DIR}/dos_Ge73Sn143_66pctSn.png" \
    --no-legend \
    --width 6 --height 4 \
    --xmin -10 --xmax 5 \
    --title "DOS: Ge73Sn143 (66% Sn, amorphous)" \
    || echo "WARNING: sumo-dosplot failed for 65_ calculation"

# ---- Calculation 3: Ge22Sn194 (~90% Sn) ----
echo ""
echo "=== Processing Ge22Sn194 (90% Sn) ==="
unzip_if_needed "${REPO_DIR}/90_vasprun.xml.zip" "${REPO_DIR}/90_vasprun.xml"
unzip_if_needed "${REPO_DIR}/90_DOSCAR.zip"       "${REPO_DIR}/90_DOSCAR"

sumo-dosplot \
    --code vasp \
    --filenames 90_vasprun.xml \
    --output "${OUT_DIR}/dos_Ge22Sn194_90pctSn.png" \
    --no-legend \
    --width 6 --height 4 \
    --xmin -10 --xmax 5 \
    --title "DOS: Ge22Sn194 (90% Sn, amorphous)" \
    || echo "WARNING: sumo-dosplot failed for 90_ calculation"

echo ""
echo "=== DOS plots complete. Output in: ${OUT_DIR} ==="
