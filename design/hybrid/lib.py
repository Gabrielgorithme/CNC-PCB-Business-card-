"""Shared drawing helpers for the hybrid (aluminium + PCB) card mockups.
10 SVG units = 1 mm, the convention of the first card's artwork. Geometry is built with shapely so every outline
respects the two processes: no inside corner tighter than R0.5 (1 mm router bit at the PCB fab, 1 mm end mill here)."""
import math, base64, io, pathlib, sys
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, box, Point, LineString
from shapely import affinity

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "lettering"))
import isocp  # noqa: E402  (ISOCP single-line strokes, as engraved on the first card)

W, H, R = 856, 540, 32
CARD_W, CARD_H = 85.6, 53.98
ENG, ENG2, CUT = "#3f454c", "#6f767f", "#0f1113"
GOLD, GOLDF = "url(#gold)", "url(#goldf)"
MASK, RELIEF, RELIEF_HI = "#0c0d0f", "#191b1f", "#3a3e45"
FR4 = "#b3ab7e"
SANS = "font-family=\"'DejaVu Sans Condensed','DejaVu Sans',Arial,sans-serif\""

# two dots for ':' (the card font has none)
_dot = isocp.G["."]
isocp.G[":"] = {"w": _dot["w"], "sb": _dot["sb"],
                "s": _dot["s"] + [[[x, y + isocp.CAP * 0.55] for x, y in s] for s in _dot["s"]]}

CARD = box(0, 0, W, H).buffer(-R).buffer(R, 32)


# ------------------------------------------------------------------ geometry
def rounded(g, r):
    """Round every convex and concave corner to radius r."""
    return g.buffer(-r, 16).buffer(r, 16).buffer(r, 16).buffer(-r, 16)

def mirror(g):
    return affinity.scale(g, xfact=-1, yfact=1, origin=(W / 2, 0))

def path(g):
    """SVG path data for any shapely geometry."""
    if g.is_empty: return ""
    t = g.geom_type
    if t == "Polygon":
        return " ".join("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in ring.coords) + " Z" for ring in [g.exterior, *g.interiors])
    if t in ("Point", "MultiPoint"): return ""
    if t in ("LineString", "LinearRing"):
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in g.coords)
    return " ".join(path(p) for p in g.geoms)

def circle(cx, cy, r):
    return Point(cx, cy).buffer(r, 64)

def rrect(x0, y0, x1, y1, r):
    return box(x0, y0, x1, y1).buffer(-r).buffer(r, 16)


# ------------------------------------------------------------------ rendering of the two materials
def _png(arr):
    buf = io.BytesIO(); Image.fromarray(arr).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def alu_image(height_fn, px_per_mm=14, seed=1):
    """Shaded aluminium face from a height field in mm (same lighting model as v3)."""
    nx, ny = int(CARD_W * px_per_mm), int(CARD_H * px_per_mm)
    x, y = np.meshgrid(np.arange(nx) / px_per_mm, np.arange(ny) / px_per_mm)
    h = height_fn(x, y) if height_fn else np.zeros_like(x)
    gy, gx = np.gradient(h * 2.6, 1 / px_per_mm)
    n = np.dstack([-gx, -gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array([-0.5, -0.62, 0.6]); L /= np.linalg.norm(L)
    Hv = L + np.array([0, 0, 1.0]); Hv /= np.linalg.norm(Hv)
    diff = np.clip(n @ L, 0, 1); spec = np.clip(n @ Hv, 0, 1) ** 60
    rng = np.random.default_rng(seed)
    brushed = np.repeat(rng.normal(0, 1, (ny, 1)), nx, axis=1) * 0.006 + rng.normal(0, 0.005, (ny, nx))
    sweep = 0.06 * np.cos((x * 0.9 + y * 1.4) / 14.0)
    v = np.clip(0.40 + 0.52 * diff / L[2] * 0.66 + 0.55 * spec + brushed + sweep + h * 0.6, 0, 1)
    rgb = np.dstack([v * 0.965, v * 0.98, v * 1.0])
    return _png((rgb * 255).astype(np.uint8))

def mask_image(seed=3):
    """Matte black solder mask: near-black with a faint grain and a soft sheen."""
    nx, ny = 428, 270
    x, y = np.meshgrid(np.arange(nx), np.arange(ny))
    rng = np.random.default_rng(seed)
    v = 0.050 + rng.normal(0, 0.006, (ny, nx)) + 0.022 * np.cos((x * 0.9 + y * 1.4) / 70.0 + 1.0)
    v = np.clip(v, 0, 1)
    rgb = np.dstack([v * 0.97, v * 0.99, v * 1.06])
    return _png((np.clip(rgb, 0, 1) * 255).astype(np.uint8))

def ripple(cx, cy, band_y=None, lam=2.0, amp=0.12, pocket_r=14.2):
    """Concentric ripple height field centred on the spring (mm). band_y: flat name band below it."""
    def f(x, y):
        r = np.hypot(x - cx, y - cy)
        env = np.clip((r - pocket_r) / 1.5, 0, 1) * np.exp(-r / 70.0)
        band = np.clip((band_y - 0.6 - y) / 1.2, 0, 1) if band_y else 1.0
        return -amp * (0.5 - 0.5 * np.cos(2 * np.pi * r / lam)) * env * band
    return f


# ------------------------------------------------------------------ lettering and line work
def text_width(s, cap, track=0.0):
    k = cap * 10 / isocp.CAP
    _, w = isocp.layout(s, track * 10 / k)
    return w * k - track * 10

def T(x, y, s, cap, color=ENG, anchor="start", track=0.0, wt=None, extra=""):
    """Single-line ISOCP text. cap = capital height in mm, track = extra letter spacing in mm."""
    k = cap * 10 / isocp.CAP
    strokes, w = isocp.layout(s, track * 10 / k)
    w = w * k - track * 10
    dx = {"start": 0, "middle": -w / 2, "end": -w}[anchor]
    d = " ".join("M" + " L".join(f"{x + dx + px * k:.2f},{y - py * k:.2f}" for px, py in st) for st in strokes)
    sw = wt if wt else max(1.0, cap * 10 / 9)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'

def P(d, w=1.3, stroke=ENG, fill="none", extra=""):
    return f'<path d="{d}" stroke="{stroke}" stroke-width="{w}" fill="{fill}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'

def relief(d, w=1.6):
    """Copper under black mask: a tone-on-tone ridge that catches the light on one side."""
    return (f'<path d="{d}" fill="none" stroke="{RELIEF_HI}" stroke-width="{w * 0.5:.2f}" transform="translate(-0.7,-0.8)" opacity=".55" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{RELIEF}" stroke-width="{w:.2f}" stroke-linecap="round"/>')

def spiral_pts(cx, cy, r0, r1, sweep, phase, flip=1, n=70):
    return [(cx + (r0 + (r1 - r0) * i / n) * math.cos(math.radians(phase + flip * sweep * i / n)),
             cy + (r0 + (r1 - r0) * i / n) * math.sin(math.radians(phase + flip * sweep * i / n))) for i in range(n + 1)]

def pl(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

def spring(cx, cy, flip=1, label=None):
    """The Ø26 orthoplanar flexure, drawn as on v3."""
    o = [f'<circle cx="{cx}" cy="{cy}" r="133" fill="#00000030"/>',
         f'<circle cx="{cx}" cy="{cy}" r="130" fill="url(#pocket)" stroke="#565c64" stroke-width="1.5"/>',
         f'<path d="M{cx-126},{cy-30} A130,130 0 0 1 {cx+30},{cy-126}" stroke="#2a2e33" stroke-width="5" fill="none" opacity=".35"/>']
    for k in range(3):
        d = pl(spiral_pts(cx, cy, 62, 118, 205, k * 120 - 90, flip))
        o.append(f'<path d="{d}" fill="none" stroke="{CUT}" stroke-width="20" stroke-linecap="round"/>')   # 2 mm slots
        o.append(f'<path d="{d}" fill="none" stroke="#e9ecef" stroke-width="1" opacity=".5" transform="translate(3.2,3.6)" stroke-linecap="round"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="48" fill="url(#boss)" stroke="#5d646c" stroke-width="1.2"/>')
    if label: o.append(T(cx, cy + 13, label, 2.6, ENG, "middle", 0.7))
    return "\n".join(o)

def hole(hx, hy):
    return (f'<circle cx="{hx}" cy="{hy}" r="15" fill="{CUT}" stroke="#30353a" stroke-width="1.5"/>'
            f'<circle cx="{hx}" cy="{hy}" r="17.5" fill="none" stroke="#f1f3f5" stroke-width="1.2" opacity=".8"/>')

def rings(cx, cy, allowed, r_from, r_to, step=20, gold_until=None, w0=4.4, w1=1.3, offset=0, kind="auto"):
    """Concentric arcs clipped to `allowed`. Gold near the joint, thinning out, then black-on-black relief."""
    o = []
    r = math.ceil((r_from - offset) / step) * step + offset
    while r <= r_to:
        arc = circle(cx, cy, r).exterior.intersection(allowed)
        if not arc.is_empty:
            t = (r - r_from) / max(1, (gold_until or r_to) - r_from)
            if kind == "relief" or (gold_until and r > gold_until):
                o.append(relief(path(arc), 1.5))
            else:
                o.append(P(path(arc), max(w1, w0 + (w1 - w0) * t), GOLD))
        r += step
    return "\n".join(o)

def coil(cx, cy, r_out, r_in, pitch=6.0, w=3.0, flip=1, phase=-90):
    """Round planar NFC antenna (Archimedean spiral). Turn count is indicative; it gets tuned to the chip later."""
    turns = (r_out - r_in) / pitch
    n = int(turns * 96)
    pts = [(cx + (r_out - pitch * turns * i / n) * math.cos(math.radians(phase) + flip * 2 * math.pi * turns * i / n),
            cy + (r_out - pitch * turns * i / n) * math.sin(math.radians(phase) + flip * 2 * math.pi * turns * i / n)) for i in range(n + 1)]
    return P(pl(pts), w, GOLD), pts[0], pts[-1]

def rect_coil(x0, y0, x1, y1, turns, pitch=6.0, w=3.0, r=14):
    """Rounded-rectangle NFC antenna drawn as nested loops joined by a jog (reads as a spiral)."""
    o = []
    for i in range(turns):
        d = i * pitch
        g = rrect(x0 + d, y0 + d, x1 - d, y1 - d, max(3, r - d))
        ring = g.exterior.difference(box(x0 + d - 2, (y0 + y1) / 2 - 4, x0 + d + 2, (y0 + y1) / 2 + 2))
        o.append(P(path(ring), w, GOLD))
        if i < turns - 1:
            o.append(P(f"M{x0+d:.1f},{(y0+y1)/2-4:.1f} L{x0+d+pitch:.1f},{(y0+y1)/2+2:.1f}", w, GOLD))
    return "\n".join(o)

def via(x, y, r=2.2, pad=4.2):
    """Plated through hole: gold annular ring, open hole. Lets a pinpoint of light through."""
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pad}" fill="{GOLDF}"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#050506"/>'

def smd(x, y, w, h, label=None, body="#1b1c20", rot=0, lx=0, ly=0):
    """A surface-mount part seen from above (body + tinned ends), with a gold designator."""
    o = [f'<g transform="translate({x},{y}) rotate({rot})"><rect x="{-w/2-2}" y="{-h/2}" width="{w+4}" height="{h}" fill="#c9cdd2"/>'
         f'<rect x="{-w/2}" y="{-h/2-.5}" width="{w}" height="{h+1}" rx="1" fill="{body}" stroke="#34373d" stroke-width=".8"/></g>']
    if label: o.append(T(x + lx, y + ly, label, 0.8, GOLD, "middle"))
    return "".join(o)

def window(geom, ghost_svg, backlit=False, led=None):
    """Bare FR-4 window (no mask, no outer copper). Inner-layer copper shows faintly in reflected light
    and as a crisp silhouette when lit from behind."""
    d = path(geom)
    cid = f"w{abs(hash(d)) % 99999}"
    o = [f'<clipPath id="{cid}"><path d="{d}"/></clipPath>']
    if backlit:
        o.append(f'<path d="{d}" fill="#ffb347" filter="url(#glow)" opacity=".9"/>')
        o.append(f'<path d="{d}" fill="url(#lit)"/>')
        if led:
            o.append(f'<g clip-path="url(#{cid})"><circle cx="{led[0]}" cy="{led[1]}" r="{led[2]}" fill="url(#led)"/></g>')
        o.append(f'<g clip-path="url(#{cid})" style="--ink:#170a00" opacity=".96">{ghost_svg("#170a00")}</g>')
        o.append(f'<path d="{d}" fill="none" stroke="#3a1c00" stroke-width="1.2"/>')
    else:
        o.append(f'<path d="{d}" fill="{FR4}"/><path d="{d}" fill="url(#weave)" opacity=".55"/>')
        o.append(f'<g clip-path="url(#{cid})" opacity=".30">{ghost_svg("#4a3b22")}</g>')
        o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-width="2.2" opacity=".55"/>'
                 f'<path d="{d}" fill="none" stroke="#e9e3bf" stroke-width=".7" opacity=".5" transform="translate(.8,.9)"/>')
    return "\n".join(o)

def qr(url, x, y, size, style="gold"):
    """QR in normal polarity (dark modules on a light field) so every phone reads it.
    gold: an ENIG plate with the dark modules left as black mask. white: white silkscreen, no copper at all."""
    import segno
    m = [list(r) for r in segno.make(url, error="l").matrix]
    n = len(m); c = size / n; q = 2.2 * c
    light = GOLDF if style == "gold" else "#eef0ee"
    o = [f'<rect x="{x-q:.1f}" y="{y-q:.1f}" width="{size+2*q:.1f}" height="{size+2*q:.1f}" rx="3" fill="{light}"/>']
    if style == "alu":      # engraved in the aluminium, filled with black paint, re-surfaced (as on the first card)
        o = [f'<rect x="{x-q:.1f}" y="{y-q:.1f}" width="{size+2*q:.1f}" height="{size+2*q:.1f}" rx="5" fill="#eceef1" stroke="{ENG2}" stroke-width="1"/>']
    for j, row in enumerate(m):
        for i, v in enumerate(row):
            if v: o.append(f'<rect x="{x+i*c:.2f}" y="{y+j*c:.2f}" width="{c+.25:.2f}" height="{c+.25:.2f}" fill="{'#24282d' if style == 'alu' else MASK}"/>')
    return "\n".join(o), n

# ---- drawing-office symbols (from v3, engraved on the aluminium)
def gdt_symbol(kind, x, y, col=ENG):
    if kind == "flatness": return P(f"M{x-8},{y+5} l5,-10 h11 l-5,10 z", 1.4, col)
    if kind == "position": return P(f"M{x-10},{y} h20 M{x},{y-10} v20", 1.3, col) + f'<circle cx="{x}" cy="{y}" r="5.5" fill="none" stroke="{col}" stroke-width="1.4"/>'
    if kind == "profile":  return P(f"M{x-8},{y+4} a8,8 0 0 1 16,0 z", 1.4, col)
    if kind == "symmetry": return P(f"M{x-8},{y} h16 M{x-5},{y-5} h10 M{x-5},{y+5} h10", 1.4, col)

def fcf(x, y, kind, tol, datums=(), h=24, col=ENG):
    cells = [26, 16 + 8.4 * len(tol)] + [24] * len(datums)
    o, cx = [], x
    for i, wc in enumerate(cells):
        o.append(f'<rect x="{cx}" y="{y}" width="{wc}" height="{h}" fill="none" stroke="{col}" stroke-width="1.4"/>')
        if i == 0: o.append(gdt_symbol(kind, cx + wc / 2, y + h / 2, col))
        elif i == 1: o.append(T(cx + wc / 2, y + 17, tol, 1.02, col, "middle"))
        else: o.append(T(cx + wc / 2, y + 17.5, datums[i - 2], 1.1, col, "middle"))
        cx += wc
    return "\n".join(o), cx - x

def arrow(x, y, ang, col=ENG):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    p = lambda dx, dy: f"{x + dx*c - dy*s:.1f},{y + dx*s + dy*c:.1f}"
    return f'<path d="M{x},{y} L{p(-11,-3.4)} L{p(-11,3.4)} z" fill="{col}"/>'

def ruler(x_from, x_to, col, numbers=True, wt=1.0):
    """mm ruler along the bottom edge. Called once per material so the scale runs across the joint."""
    o = []
    for i in range(0, 86):
        if not (x_from <= i * 10 <= x_to): continue
        hh = 15 if i % 10 == 0 else 10 if i % 5 == 0 else 6
        o.append(P(f"M{i*10},{H} v{-hh}", wt, col))
        if numbers and i % 10 == 0 and 0 < i < 85 and x_from <= i * 10 + 3 and i * 10 + 14 <= x_to:
            o.append(T(i * 10 + 3, H - 17, str(i), 0.66, col))
    return "\n".join(o)

def vernier(xj, y0, alu_side=1, n=10, main=10.0):
    """Vernier across a vertical joint: main scale engraved on the aluminium, 9/10 scale etched on the PCB.
    The pair of lines that coincide gives the vertical assembly error of that very card, in tenths of a mm."""
    o = []
    for i in range(n + 1):
        L = 22 if i % 5 == 0 else 14
        o.append(P(f"M{xj + alu_side*3},{y0 + i*main:.1f} h{alu_side*L}", 1.1, ENG))
        o.append(P(f"M{xj - alu_side*3},{y0 + i*main*0.9:.1f} h{-alu_side*L}", 1.2, GOLD))
    return "\n".join(o)


# ------------------------------------------------------------------ card assembly
DEFS = f'''<radialGradient id="pocket"><stop offset="0" stop-color="#aeb3b9"/><stop offset=".8" stop-color="#949aa1"/><stop offset="1" stop-color="#70767e"/></radialGradient>
<linearGradient id="boss" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#e6e8eb"/><stop offset="1" stop-color="#b4b9bf"/></linearGradient>
<linearGradient id="gold" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">
<stop offset="0" stop-color="#b98c2e"/><stop offset=".18" stop-color="#f3d77c"/><stop offset=".34" stop-color="#c79a3a"/><stop offset=".52" stop-color="#ffe9a0"/><stop offset=".7" stop-color="#cfa244"/><stop offset=".86" stop-color="#f0d070"/><stop offset="1" stop-color="#a97c26"/></linearGradient>
<linearGradient id="goldf" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="{H}">
<stop offset="0" stop-color="#c79b3c"/><stop offset=".3" stop-color="#ecd07a"/><stop offset=".55" stop-color="#d7b055"/><stop offset=".8" stop-color="#f1d987"/><stop offset="1" stop-color="#bd8f33"/></linearGradient>
<radialGradient id="lit" gradientUnits="objectBoundingBox" cx=".5" cy=".5" r=".75"><stop offset="0" stop-color="#ffe2a0"/><stop offset=".6" stop-color="#ffb648"/><stop offset="1" stop-color="#e07a12"/></radialGradient>
<radialGradient id="led"><stop offset="0" stop-color="#fff6d8"/><stop offset=".25" stop-color="#ffd27a" stop-opacity=".9"/><stop offset="1" stop-color="#ffb648" stop-opacity="0"/></radialGradient>
<radialGradient id="star"><stop offset="0" stop-color="#fff8e0"/><stop offset=".35" stop-color="#ffd98a" stop-opacity=".8"/><stop offset="1" stop-color="#ffb648" stop-opacity="0"/></radialGradient>
<pattern id="weave" width="5" height="5" patternUnits="userSpaceOnUse"><path d="M0,1.2 H5 M0,3.7 H5" stroke="#8d8760" stroke-width=".7"/><path d="M1.2,0 V5 M3.7,0 V5" stroke="#d4cc9c" stroke-width=".6"/></pattern>
<filter id="sh" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-opacity=".6"/></filter>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="7"/></filter>
<filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="14"/></filter>
<clipPath id="clip"><rect width="{W}" height="{H}" rx="{R}"/></clipPath>'''

def card(alu_img, alu, pcb, pcb_body, alu_body, joint_gold=False, backlit=None, bg=None, extra_top=""):
    """Assemble one face. alu / pcb: shapely regions. Bodies are SVG drawn in card coordinates and clipped to their material.
    backlit: SVG drawn over a darkened card (windows, pinholes) for the held-to-the-light view."""
    seam = alu.boundary.intersection(CARD.buffer(-1.5))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="-30 -30 {W+60} {H+60}">',
         f'<defs>{DEFS}<clipPath id="alu"><path d="{path(alu)}"/></clipPath><clipPath id="pcb"><path d="{path(pcb)}"/></clipPath></defs>']
    if bg: o.append(f'<rect x="-30" y="-30" width="{W+60}" height="{H+60}" fill="{bg}"/>')
    o.append(f'<rect width="{W}" height="{H}" rx="{R}" fill="#c9ccd0" filter="url(#sh)"/>')
    o.append(f'<g clip-path="url(#clip)">')
    o.append(f'<g clip-path="url(#pcb)"><image href="{mask_image()}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none"/>{pcb_body}</g>')
    o.append(f'<g clip-path="url(#alu)"><image href="{alu_img}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none"/>{alu_body}</g>')
    # the joint: glue line, lit aluminium edge, optional gold-plated PCB edge
    o.append(f'<path d="{path(seam)}" fill="none" stroke="#000" stroke-width="2.4" opacity=".75"/>')
    o.append(f'<g clip-path="url(#alu)"><path d="{path(seam)}" fill="none" stroke="#fbfcfd" stroke-width="3.2" opacity=".65" transform="translate(-1.2,-1.2)"/></g>')
    if joint_gold:
        o.append(f'<g clip-path="url(#pcb)"><path d="{path(seam)}" fill="none" stroke="{GOLD}" stroke-width="5"/></g>')
        o.append(f'<path d="{path(seam)}" fill="none" stroke="#000" stroke-width="1.1" opacity=".8"/>')
    o.append(extra_top)
    if backlit is not None:
        o.append(f'<rect width="{W}" height="{H}" fill="#020203" opacity=".86"/>{backlit}')
    o.append('</g>')
    if backlit is None:
        o.append(f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="{R-1}" fill="none" stroke="#fafbfc" stroke-width="2.5" opacity=".35"/>')
    o.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="{R}" fill="none" stroke="#50565d" stroke-width="1" opacity=".6"/></svg>')
    return "\n".join(o)


SILK = "#eef0ee"

def arc_text(cx, cy, r_base, th_mid_deg, s, cap, color, track=0.0, wt=None, inward=False):
    """Text set along a circle. Default: read clockwise, capitals pointing outward.
    inward=True: read counter-clockwise, capitals pointing at the centre (for the lower half of a circle)."""
    k = cap * 10 / isocp.CAP
    strokes, w = isocp.layout(s, track * 10 / k)
    w = w * k - track * 10
    d_ = -1 if inward else 1
    th0 = math.radians(th_mid_deg) - d_ * (w / 2) / r_base
    d = " ".join("M" + " L".join(f"{cx + (r_base + d_*py*k) * math.cos(th0 + d_*px*k/r_base):.2f},{cy + (r_base + d_*py*k) * math.sin(th0 + d_*px*k/r_base):.2f}" for px, py in st) for st in strokes)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{wt or max(1.0, cap*10/9):.2f}" stroke-linecap="round" stroke-linejoin="round"/>'

def arc_pts(cx, cy, r, a0, a1, n=48):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def fiducial(x, y):
    return f'<circle cx="{x}" cy="{y}" r="12" fill="{FR4}"/><circle cx="{x}" cy="{y}" r="12" fill="none" stroke="#000" stroke-width="1.6" opacity=".5"/><circle cx="{x}" cy="{y}" r="5" fill="{GOLDF}"/>'
