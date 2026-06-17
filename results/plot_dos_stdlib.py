"""
DOS plotter — stdlib only (no matplotlib/numpy required).
Reads DOSCAR directly from .zip archives and writes SVG files.

Output files (in the same directory as this script):
  dos_individual.svg   - 3-panel subplot, one DOS per composition
  dos_overlay.svg      - all compositions overlaid on one axis
  dos_gap_zoom.svg     - gap region ±1.5 eV around E_F
"""

import zipfile
import os
import math

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO, "results")
os.makedirs(RESULTS, exist_ok=True)

CALCULATIONS = [
    {
        "label": "Ge43Sn173 (80% Sn)",
        "zip":   os.path.join(REPO, "DOSCAR.zip"),
        "color": "#1f77b4",
    },
    {
        "label": "Ge73Sn143 (66% Sn)",
        "zip":   os.path.join(REPO, "65_DOSCAR.zip"),
        "color": "#ff7f0e",
    },
    {
        "label": "Ge22Sn194 (90% Sn)",
        "zip":   os.path.join(REPO, "90_DOSCAR.zip"),
        "color": "#2ca02c",
    },
]


# ── DOSCAR parser ──────────────────────────────────────────────────────────────

def read_doscar(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        doscar_name = next(
            (n for n in names
             if os.path.basename(n).upper() == "DOSCAR"
             or os.path.basename(n).upper().endswith("DOSCAR")),
            names[0],
        )
        raw = zf.read(doscar_name).decode("utf-8", errors="replace")

    lines = raw.splitlines()
    ispin = int(lines[0].split()[2])
    efermi = float(lines[5].split()[2])

    n_cols = 3 + 2 * (ispin - 1)
    energies, dos = [], []
    for line in lines[6:]:
        parts = line.split()
        if len(parts) != n_cols:
            break
        energies.append(float(parts[0]))
        dos.append(float(parts[1]))

    return energies, dos, efermi


# ── Gaussian smoothing (no numpy) ──────────────────────────────────────────────

def gaussian_smooth(y, sigma=2.5):
    ks = max(1, int(6 * sigma))
    if ks % 2 == 0:
        ks += 1
    half = ks // 2
    kernel = [math.exp(-0.5 * (i / sigma) ** 2) for i in range(-half, half + 1)]
    s = sum(kernel)
    kernel = [k / s for k in kernel]
    result = []
    n = len(y)
    for i in range(n):
        val = 0.0
        for j, w in enumerate(kernel):
            idx = i - half + j
            if 0 <= idx < n:
                val += y[idx] * w
        result.append(val)
    return result


# ── SVG generation helpers ─────────────────────────────────────────────────────

W, H = 700, 320   # SVG canvas per panel
PAD = dict(left=65, right=20, top=30, bottom=50)


def data_to_svg(x_vals, y_vals, x_min, x_max, y_min, y_max):
    """Convert data coords to SVG pixel coords."""
    pw = W - PAD["left"] - PAD["right"]
    ph = H - PAD["top"] - PAD["bottom"]
    px = [PAD["left"] + (x - x_min) / (x_max - x_min) * pw for x in x_vals]
    py = [PAD["top"] + ph - (y - y_min) / (y_max - y_min) * ph for y in y_vals]
    return list(zip(px, py))


def polyline_path(points):
    if not points:
        return ""
    parts = [f"M {points[0][0]:.2f},{points[0][1]:.2f}"]
    parts += [f"L {p[0]:.2f},{p[1]:.2f}" for p in points[1:]]
    return " ".join(parts)


def fill_path(points, y_min, x_min, x_max):
    """Closed path for area fill (line + baseline)."""
    pw = W - PAD["left"] - PAD["right"]
    ph = H - PAD["top"] - PAD["bottom"]
    baseline_y = PAD["top"] + ph  # y=0 pixel

    if not points:
        return ""
    path = polyline_path(points)
    path += f" L {points[-1][0]:.2f},{baseline_y:.2f}"
    path += f" L {points[0][0]:.2f},{baseline_y:.2f} Z"
    return path


def axis_svg(x_min, x_max, y_max, x_ticks=None, title="", xlabel="E - E_F (eV)", ylabel="DOS (states/eV)"):
    pw = W - PAD["left"] - PAD["right"]
    ph = H - PAD["top"] - PAD["bottom"]
    lx = PAD["left"]
    rx = PAD["left"] + pw
    ty = PAD["top"]
    by = PAD["top"] + ph

    lines = []

    # Box / axes
    lines.append(f'<rect x="{lx}" y="{ty}" width="{pw}" height="{ph}" '
                 f'fill="white" stroke="#333" stroke-width="1"/>')

    # Zero line (E_F)
    if x_min <= 0 <= x_max:
        zero_x = lx + (0 - x_min) / (x_max - x_min) * pw
        lines.append(f'<line x1="{zero_x:.2f}" y1="{ty}" x2="{zero_x:.2f}" y2="{by}" '
                     f'stroke="#999" stroke-width="0.8" stroke-dasharray="4,3"/>')

    # y=0 baseline
    lines.append(f'<line x1="{lx}" y1="{by}" x2="{rx}" y2="{by}" '
                 f'stroke="#bbb" stroke-width="0.5"/>')

    # X ticks
    if x_ticks is None:
        x_ticks = [i for i in range(int(math.ceil(x_min)), int(math.floor(x_max)) + 1)]
    for t in x_ticks:
        if x_min <= t <= x_max:
            tx = lx + (t - x_min) / (x_max - x_min) * pw
            lines.append(f'<line x1="{tx:.2f}" y1="{by}" x2="{tx:.2f}" y2="{by+5}" '
                         f'stroke="#333" stroke-width="1"/>')
            lines.append(f'<text x="{tx:.2f}" y="{by+16}" text-anchor="middle" '
                         f'font-size="11" font-family="sans-serif">{t}</text>')

    # Y ticks (0, y_max/2, y_max)
    for frac, label in [(0, "0"), (0.5, f"{y_max/2:.0f}"), (1.0, f"{y_max:.0f}")]:
        yv = frac * y_max
        ypx = by - frac * ph
        lines.append(f'<line x1="{lx-5}" y1="{ypx:.2f}" x2="{lx}" y2="{ypx:.2f}" '
                     f'stroke="#333" stroke-width="1"/>')
        lines.append(f'<text x="{lx-8}" y="{ypx+4:.2f}" text-anchor="end" '
                     f'font-size="10" font-family="sans-serif">{label}</text>')

    # Axis labels
    cx = lx + pw / 2
    lines.append(f'<text x="{cx:.2f}" y="{by+36}" text-anchor="middle" '
                 f'font-size="12" font-family="sans-serif">{xlabel}</text>')
    cy = ty + ph / 2
    lines.append(f'<text x="14" y="{cy:.2f}" text-anchor="middle" '
                 f'font-size="12" font-family="sans-serif" '
                 f'transform="rotate(-90,14,{cy:.2f})">{ylabel}</text>')

    if title:
        lines.append(f'<text x="{cx:.2f}" y="{ty-8}" text-anchor="middle" '
                     f'font-size="12" font-family="sans-serif" font-weight="bold">{title}</text>')

    return "\n".join(lines)


def legend_item(cx, cy, color, label):
    return (f'<rect x="{cx}" y="{cy-8}" width="14" height="10" fill="{color}" opacity="0.7"/>'
            f'<text x="{cx+18}" y="{cy}" font-size="11" font-family="sans-serif">{label}</text>')


def make_svg(panels, total_h, title=""):
    """Wrap SVG panels."""
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total_h}">']
    svg.append(f'<rect width="{W}" height="{total_h}" fill="white"/>')
    if title:
        svg.append(f'<text x="{W//2}" y="22" text-anchor="middle" '
                   f'font-size="14" font-weight="bold" font-family="sans-serif">{title}</text>')
    return svg


# ── Load and smooth data ───────────────────────────────────────────────────────

datasets = []
for calc in CALCULATIONS:
    print(f"Parsing {calc['zip']} …")
    energies, dos, efermi = read_doscar(calc["zip"])
    shifted = [e - efermi for e in energies]
    smoothed = gaussian_smooth(dos, sigma=2.0)
    datasets.append({**calc, "energies": shifted, "dos": smoothed, "efermi": efermi})
    print(f"  E_F = {efermi:.4f} eV,  NEDOS = {len(energies)}")


def filter_range(ds, emin, emax):
    e = [x for x in ds["energies"] if emin <= x <= emax]
    d = [ds["dos"][i] for i, x in enumerate(ds["energies"]) if emin <= x <= emax]
    return e, d


# ── Plot 1: Individual 3-panel ─────────────────────────────────────────────────

total_h = 3 * H + 40
svg = make_svg(None, total_h, "Total DOS — Amorphous Ge/Sn Alloys")
svg.append(f'<rect width="{W}" height="{total_h}" fill="white"/>')
svg.append(f'<text x="{W//2}" y="22" text-anchor="middle" '
           f'font-size="14" font-weight="bold" font-family="sans-serif">'
           f'Total DOS — Amorphous Ge/Sn Alloys</text>')

for panel_i, ds in enumerate(datasets):
    offset_y = 30 + panel_i * H
    svg.append(f'<g transform="translate(0,{offset_y})">')

    ex, dx = filter_range(ds, -6, 6)
    y_max = max(dx) * 1.05 if dx else 1.0

    svg.append(axis_svg(-6, 6, y_max, title=ds["label"]))
    pts = data_to_svg(ex, dx, -6, 6, 0, y_max)
    fp = fill_path(pts, 0, -6, 6)
    svg.append(f'<path d="{fp}" fill="{ds["color"]}" opacity="0.3"/>')
    svg.append(f'<path d="{polyline_path(pts)}" fill="none" '
               f'stroke="{ds["color"]}" stroke-width="1.5"/>')
    svg.append('</g>')

svg.append('</svg>')
out = os.path.join(RESULTS, "dos_individual.svg")
with open(out, "w") as f:
    f.write("\n".join(svg))
print(f"Saved {out}")


# ── Plot 2: Overlay ────────────────────────────────────────────────────────────

total_h = H + 40
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total_h}">',
       f'<rect width="{W}" height="{total_h}" fill="white"/>',
       f'<text x="{W//2}" y="22" text-anchor="middle" '
       f'font-size="14" font-weight="bold" font-family="sans-serif">'
       f'Total DOS Overlay — Amorphous Ge/Sn Alloys</text>',
       '<g transform="translate(0,30)">']

all_dos_vals = []
for ds in datasets:
    _, dx = filter_range(ds, -6, 6)
    all_dos_vals.extend(dx)
y_max = max(all_dos_vals) * 1.05 if all_dos_vals else 1.0

svg.append(axis_svg(-6, 6, y_max))

for ds in datasets:
    ex, dx = filter_range(ds, -6, 6)
    pts = data_to_svg(ex, dx, -6, 6, 0, y_max)
    svg.append(f'<path d="{polyline_path(pts)}" fill="none" '
               f'stroke="{ds["color"]}" stroke-width="1.8" opacity="0.85"/>')

# Legend
for i, ds in enumerate(datasets):
    svg.append(legend_item(PAD["left"] + 10, PAD["top"] + 20 + i * 18,
                           ds["color"], ds["label"]))

svg.append('</g></svg>')
out = os.path.join(RESULTS, "dos_overlay.svg")
with open(out, "w") as f:
    f.write("\n".join(svg))
print(f"Saved {out}")


# ── Plot 3: Gap zoom ───────────────────────────────────────────────────────────

total_h = H + 40
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total_h}">',
       f'<rect width="{W}" height="{total_h}" fill="white"/>',
       f'<text x="{W//2}" y="22" text-anchor="middle" '
       f'font-size="14" font-weight="bold" font-family="sans-serif">'
       f'DOS near E_F — Gap Region</text>',
       '<g transform="translate(0,30)">']

all_dos_vals = []
for ds in datasets:
    _, dx = filter_range(ds, -1.5, 1.5)
    all_dos_vals.extend(dx)
y_max = max(all_dos_vals) * 1.15 if all_dos_vals else 1.0

x_ticks = [-1.5, -1.0, -0.5, 0, 0.5, 1.0, 1.5]
svg.append(axis_svg(-1.5, 1.5, y_max, x_ticks=x_ticks, title="Gap region (E_F = 0)"))

for ds in datasets:
    ex, dx = filter_range(ds, -1.5, 1.5)
    pts = data_to_svg(ex, dx, -1.5, 1.5, 0, y_max)
    fp = fill_path(pts, 0, -1.5, 1.5)
    svg.append(f'<path d="{fp}" fill="{ds["color"]}" opacity="0.2"/>')
    svg.append(f'<path d="{polyline_path(pts)}" fill="none" '
               f'stroke="{ds["color"]}" stroke-width="1.8"/>')

for i, ds in enumerate(datasets):
    svg.append(legend_item(PAD["left"] + 10, PAD["top"] + 20 + i * 18,
                           ds["color"], ds["label"]))

svg.append('</g></svg>')
out = os.path.join(RESULTS, "dos_gap_zoom.svg")
with open(out, "w") as f:
    f.write("\n".join(svg))
print(f"Saved {out}")

print("\nAll SVG DOS plots written to results/")
