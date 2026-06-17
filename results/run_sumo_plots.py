#!/usr/bin/env python3
"""
Generate DOS plots using sumo for all three GeSn VASP calculations.

Requires: pip install sumo pymatgen matplotlib

Usage:
    cd <repo_root>
    python3 results/run_sumo_plots.py
"""
import subprocess
import sys
import zipfile
import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# Install dependencies
print("Installing sumo and pymatgen...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "sumo", "pymatgen", "matplotlib", "-q"])
print("Dependencies installed.\n")

CALCS = [
    {
        "name": "Ge43Sn173",
        "label": "80% Sn (Ge43Sn173)",
        "vasprun_zip": "vasprun.xml.zip",
        "work_dir": "calc_80sn",
        "sn_pct": 80,
    },
    {
        "name": "Ge73Sn143",
        "label": "66% Sn (Ge73Sn143)",
        "vasprun_zip": "65_vasprun.xml.zip",
        "work_dir": "calc_66sn",
        "sn_pct": 66,
    },
    {
        "name": "Ge22Sn194",
        "label": "90% Sn (Ge22Sn194)",
        "vasprun_zip": "90_vasprun.xml.zip",
        "work_dir": "calc_90sn",
        "sn_pct": 90,
    },
]


def extract_vasprun(zip_path, work_dir):
    """Extract vasprun.xml from zip into work_dir, renamed to vasprun.xml."""
    os.makedirs(work_dir, exist_ok=True)
    target = os.path.join(work_dir, "vasprun.xml")
    if os.path.exists(target):
        print(f"  vasprun.xml already present in {work_dir}")
        return True
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        print(f"  Zip contains: {names}")
        xml_files = [n for n in names if "vasprun" in n.lower() and n.endswith(".xml")]
        if not xml_files:
            xml_files = [n for n in names if n.endswith(".xml")]
        if not xml_files:
            print(f"  WARNING: no xml file found in {zip_path}")
            return False
        chosen = xml_files[0]
        print(f"  Extracting {chosen} -> vasprun.xml")
        with zf.open(chosen) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)
    return True


def run_sumo_dosplot(work_dir, out_prefix, elements=None):
    """Run sumo-dosplot in work_dir, return True on success."""
    cmd = [
        "sumo-dosplot",
        "--format", "png",
        "--filename", out_prefix,
        "--gaussian", "0.05",
        "--xmin", "-4",
        "--xmax", "4",
    ]
    if elements:
        cmd += ["--elements"] + elements

    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[:2000]}")
        return False
    print(f"  stdout: {result.stdout[:500]}")
    return True


def collect_outputs(work_dir, out_prefix, dest_dir, dest_name):
    """Move generated plot files from work_dir to dest_dir with dest_name."""
    moved = []
    for f in os.listdir(work_dir):
        if f.startswith(out_prefix) and (f.endswith(".png") or f.endswith(".pdf")):
            src = os.path.join(work_dir, f)
            ext = os.path.splitext(f)[1]
            dst = os.path.join(dest_dir, dest_name + ext)
            shutil.copy2(src, dst)
            moved.append(dst)
    return moved


failed = []

for calc in CALCS:
    print(f"\n{'='*60}")
    print(f"Processing: {calc['label']}")
    print(f"{'='*60}")

    work_dir = os.path.join(BASE_DIR, calc["work_dir"])
    zip_path = os.path.join(BASE_DIR, calc["vasprun_zip"])

    # Extract vasprun.xml
    if not extract_vasprun(zip_path, work_dir):
        failed.append(calc["name"])
        continue

    out_prefix = f"dos_{calc['name']}"

    # 1. Total + element-projected DOS (most informative)
    success = run_sumo_dosplot(
        work_dir,
        out_prefix=out_prefix,
        elements=["Ge", "Sn"],
    )
    if not success:
        # Retry without element projections (in case of partial DOS issues)
        print("  Retrying without element projections...")
        success = run_sumo_dosplot(work_dir, out_prefix=out_prefix)

    if success:
        moved = collect_outputs(work_dir, out_prefix, RESULTS_DIR, f"sumo_dos_{calc['name']}")
        print(f"  Output: {moved}")
    else:
        print(f"  FAILED for {calc['name']}")
        failed.append(calc["name"])


# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
plots = [f for f in os.listdir(RESULTS_DIR) if f.startswith("sumo_dos_")]
print(f"Generated {len(plots)} plot file(s) in results/:")
for p in sorted(plots):
    print(f"  {p}")

if failed:
    print(f"\nFailed calculations: {failed}")
    sys.exit(1)
else:
    print("\nAll calculations processed successfully.")
