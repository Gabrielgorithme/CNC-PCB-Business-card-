"""Hybrid card, PCB half, rev A (first article / test coupon).

Stage 1 of 2: writes the board outline, the artwork, the windows, the plated holes and the antenna as a KiCad
board file (format of KiCad 7, which KiCad 10 opens). Stage 2 (place_parts.py, run with KiCad's own Python)
adds the library footprints of the NFC tag and routes them.

All coordinates are in millimetres in the CARD frame: origin at the card's top-left corner seen from the recto,
x to the right, y down (KiCad's own convention). The same numbers drive the aluminium half.
"""
import math, pathlib, sys, uuid
from shapely.geometry import LineString, Point, Polygon, box
from shapely import affinity

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "site")); sys.path.insert(0, str(HERE))
import isocp, coil  # noqa: E402

_dot = isocp.G["."]
isocp.G[":"] = {"w": _dot["w"], "sb": _dot["sb"], "s": _dot["s"] + [[[x, y + isocp.CAP * 0.55] for x, y in s] for s in _dot["s"]]}

# ----------------------------------------------------------------------------- shared geometry (mm)
CARD_W, CARD_H, CARD_R = 85.60, 53.98, 3.18
CARD_T, BOARD_T = 1.70, 1.20   # card and board thickness; the board sits flush with the recto on a 0.50 ledge.
# The stack-up written to the board file is a nominal split that adds up to BOARD_T; the fab's standard stack-up applies.
SPR = (19.0, 21.5)            # flexure / ripple centre
R_JOINT = 36.0                # joint = 18th ripple crest (wavelength 2 mm)
LEDGE, RIM, RIM_LEDGE = 4.0, 3.18, 1.5
GAP = 0.10                    # board is drawn this much smaller than the pocket, per side
EDGE_RECESS = 0.10            # the board's free edge stops this far inside the card's edge, so it can never stand proud of it
EDGE_X = CARD_W - EDGE_RECESS
# ---- interface with the aluminium half (see cad/hybrid/build_alu.py and cad/hybrid/README.md)
SKIM = 0.02                   # ripple crests sit this far below the faced recto; the board's top face is at crest height
SEAT_W = 0.50                 # dry seating land at the foot of the pocket wall, 0.10 inside the board's copper pull-back
GLUE_GAP = 0.08               # the rest of the ledge is this much lower: bond line, and room for copper on the board's back
COPPER_PULLBACK = 0.60        # centre lines of the artwork stay this far from the edge. Closest copper on the BACK along the joint and rims: the pin lands, 0.50
PIN_D, PIN_B_FLATS = 2.00, 0.70   # pin A round; pin B is a blade across the line A-B (diamond pin): it takes +/-0.12 on the hole spacing
PIN_TOP_BELOW, PIN_CHAMFER = 0.05, 0.15
VERNIER_A0, VERNIER_STEP_PCB, VERNIER_STEP_ALU = 27.6, 1.35, 1.50   # degrees about the flexure centre, card frame
BAND_Y = 38.4
SLOT_R, SLOT_HW, SLOT_A = 48.0, 1.3, (-18.0, 17.0)
FENCE_R = 50.6
PIN_R, PIN_A, PIN_DRILL, PIN_PAD = 38.0, (-24.0, 22.0), 2.10, 2.80   # land 2.80: its back face stays off the seat land
BGA = (76.4, 11.2)
FINGER_Y = [23.2 + 1.2 * j for j in range(12)]
FINGER_X = 82.95               # centre of the 4.5 mm edge fingers: they end 0.30 from the free edge
CAST_Y = [6.3 + 1.6 * i for i in range(8)]   # first hole 3.0 from the board corner, as JLCPCB asks for castellations
COIL = dict(x0=70.7, y0=18.4, x1=84.8, y1=47.6, turns=7, pitch=0.35, w=0.20, end_y=40.2)
COIL_END = (76.4, 40.2)       # inner end, where the antenna drops to layer 3
MARKER = (56.5, 39.6, 62.1, 41.0)
OX, OY = 100.0, 80.0          # where the card's corner sits on the KiCad sheet

def pol(r, a_deg, c=SPR):
    return (c[0] + r * math.cos(math.radians(a_deg)), c[1] + r * math.sin(math.radians(a_deg)))

def jx(y, r=R_JOINT):
    return SPR[0] + math.sqrt(r * r - (y - SPR[1]) ** 2)

def circle(c, r, res=256):
    return Point(c).buffer(r, res)

def board_shape(extra_arc=0.0, extra_rim=0.0, gap=GAP):
    """Board outline. extra_* > 0 gives what is left visible from the back once the ledge is in place."""
    g = box(SPR[0], RIM + extra_rim, CARD_W + 10, CARD_H - RIM - extra_rim).difference(circle(SPR, R_JOINT + extra_arc))
    g = g.buffer(-1.0, 64).buffer(1.0, 64)                       # R1.0 on the corners that sit in the pocket
    if gap: g = g.buffer(-gap, 64)
    return g.intersection(box(0, 0, EDGE_X, CARD_H))

PINS = [pol(PIN_R, a) for a in PIN_A]
BOARD = board_shape()
BACK_VISIBLE = board_shape(LEDGE, RIM_LEDGE, gap=0)

# ----------------------------------------------------------------------------- s-expression emitters
_n = [0]
def uid():
    _n[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"gg-card-revA-{_n[0]}"))

def P(p):
    return f"{p[0] + OX:.4f} {p[1] + OY:.4f}"

OUT = []
def line(layer, a, b, w):
    OUT.append(f'  (gr_line (start {P(a)}) (end {P(b)}) (stroke (width {w:.3f}) (type solid)) (layer "{layer}") (tstamp {uid()}))')

def polyline(layer, pts, w):
    for a, b in zip(pts, pts[1:]):
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1e-6: line(layer, a, b, w)

def poly(layer, pts, fill=True, w=0.0):
    xy = " ".join(f"(xy {P(p)})" for p in pts)
    OUT.append(f'  (gr_poly (pts {xy}) (stroke (width {w:.3f}) (type solid)) (fill {"solid" if fill else "none"}) (layer "{layer}") (tstamp {uid()}))')

def disc(layer, c, r):
    OUT.append(f'  (gr_circle (center {P(c)}) (end {P((c[0] + r, c[1]))}) (stroke (width 0) (type solid)) (fill solid) (layer "{layer}") (tstamp {uid()}))')

def shapely_lines(g):
    if g.is_empty: return []
    if g.geom_type == "LineString": return [list(g.coords)]
    if g.geom_type in ("MultiLineString", "GeometryCollection"): return [l for s in g.geoms for l in shapely_lines(s)]
    return []

def gold(layer_cu, layer_mask, pts, w, expose=0.0, min_w=0.15):
    """Copper left bare of solder mask: ENIG gold. The opening equals the copper (no bare FR-4 halo around it).
    Widths are held at 0.15 or more, except where min_w says otherwise (the coupon ladders, which exist to go below)."""
    w = max(w, min_w)
    polyline(layer_cu, pts, w); polyline(layer_mask, pts, w + 2 * expose)

# ----------------------------------------------------------------------------- lettering (ISOCP single line, as engraved)
def text(x, y, s, cap, anchor="start", track=0.0, rot=0.0, mirror=False):
    """Stroke polylines for a line of text. mirror=True flips it left-right about x (for the back face)."""
    k = cap / isocp.CAP
    strokes, w = isocp.layout(s, track / k)
    w = w * k - track
    dx = {"start": 0.0, "middle": -w / 2, "end": -w}[anchor]
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for st in strokes:
        pts = []
        for px, py in st:
            u, v = dx + px * k, -py * k
            if mirror: u = -u
            pts.append((x + u * ca - v * sa, y + u * sa + v * ca))
        out.append(pts)
    return out

def arc_text(r_base, a_mid, s, cap, track=0.0, inward=False, c=SPR):
    k = cap / isocp.CAP
    strokes, w = isocp.layout(s, track / k)
    w = w * k - track
    d = -1 if inward else 1
    a0 = math.radians(a_mid) - d * (w / 2) / r_base
    return [[(c[0] + (r_base + d * py * k) * math.cos(a0 + d * px * k / r_base),
              c[1] + (r_base + d * py * k) * math.sin(a0 + d * px * k / r_base)) for px, py in st] for st in strokes]

def mirror_x(strokes):
    return [[(CARD_W - x, y) for x, y in st] for st in strokes]

def back_arc_text(r_base, a_mid, s, cap, track=0.0):
    """Text on an arc around the flexure centre, readable from the back."""
    cv = (CARD_W - SPR[0], SPR[1])
    return mirror_x(arc_text(r_base, 180.0 - a_mid, s, cap, track, c=cv))

def gold_text(cu, mask, strokes, w, min_w=0.15):
    for st in strokes: gold(cu, mask, st, w, min_w=min_w)

# ----------------------------------------------------------------------------- decorative copper as real nets
# Every decorative trace with the pads it touches is one small net of its own ("ART_n"), so the design-rule check
# sees it as intended connections and still checks its clearance to everything else.
ART_PADS, ART_TRACKS, _parent = [], [], {}

def _key(c): return (round(c[0], 3), round(c[1], 3))
def _find(k):
    while _parent.setdefault(k, k) != k: k = _parent[k]
    return k
def _join(a, b): _parent[_find(_key(a))] = _find(_key(b))

def th_pad(c, size, drill, shape="circle", w=None, tented=False):
    """tented=True leaves the pad under solder mask on both faces: a ridge, not gold."""
    ART_PADS.append((_key(c), f'thru_hole {shape} (at {c[0]:.4f} {c[1]:.4f}) (size {w or size} {size}) (drill {drill}) (layers "*.Cu"{"" if tented else " " + chr(34) + "*.Mask" + chr(34)})' + (' (roundrect_rratio 0.25)' if shape == "roundrect" else '')))
    _find(_key(c))

def smd_pad(c, w, h, layers, shape="circle", rr=0.5):
    rrs = f" (roundrect_rratio {rr})" if shape == "roundrect" else ""
    ART_PADS.append((_key(c), f'smd {shape} (at {c[0]:.4f} {c[1]:.4f}) (size {w} {h}) (layers {layers}){rrs}'))
    _find(_key(c))

def art_trace(pts, w, a, b, expose=0.0, mask_pts=None):
    """Exposed decorative trace from the pad at a to the pad at b (pad centres; the trace may start inside the pad).
    mask_pts: the mask opening where it must stop short of the copper's end (at a via that stays under mask)."""
    _join(a, b); w = max(w, 0.15)
    ART_TRACKS.append((_key(a), pts, w))
    polyline("F.Mask", mask_pts or pts, w + 2 * expose)

def meander(xa, xb, y, amp=0.36, period=0.8):
    pts = [(xa, y)]; x = xa; up = True
    while x - period >= xb:
        pts += [(x, y - amp if up else y + amp), (x - period / 2, y - amp if up else y + amp), (x - period / 2, y)]
        x -= period / 2; up = not up
    pts.append((xb, y))
    return pts

# =============================================================================== build
def build():
    # ---- outline
    poly("Edge.Cuts", list(BOARD.exterior.coords)[:-1], fill=False, w=0.05)

    # ---- reference drawings (not fabricated): card, pocket, ledge edge, flexure, coupon notes
    card = box(0, 0, CARD_W, CARD_H).buffer(-CARD_R).buffer(CARD_R, 32)
    poly("Dwgs.User", list(card.exterior.coords)[:-1], fill=False, w=0.1)
    poly("Dwgs.User", list(board_shape(gap=0).exterior.coords)[:-1], fill=False, w=0.05)
    poly("Cmts.User", list(BACK_VISIBLE.exterior.coords)[:-1], fill=False, w=0.05)
    poly("Dwgs.User", list(circle(SPR, 13.0, 64).exterior.coords)[:-1], fill=False, w=0.1)
    for i, s in enumerate(["GG-2027-002 REV A · PCB HALF · CARD FRAME ORIGIN = CARD TOP-LEFT (RECTO)",
                           "DWGS.USER: CARD OUTLINE, NOMINAL POCKET, FLEXURE POCKET · CMTS.USER: BOARD LEFT VISIBLE BY THE LEDGE (BACK)",
                           "BOARD DRAWN 0.10 SMALLER THAN THE POCKET PER SIDE · MACHINE THE POCKET TO THE DELIVERED BOARDS"]):
        for st in text(0, CARD_H + 4 + i * 2.2, s, 1.2): polyline("Cmts.User", st, 0.12)

    keep = BOARD.buffer(-0.6)                      # copper pull-back from the routed edge (0.3 clear of the stroke edge)
    pin_ko = circle(PINS[0], PIN_PAD / 2 + 0.55, 32).union(circle(PINS[1], PIN_PAD / 2 + 0.55, 32))   # leaves a 0.3 mask web to the ring ends

    # ---- gold rings: the ripples carried on, 2 mm apart like the crests; relief rings in between (copper under mask)
    upper = keep.intersection(box(0, 0, CARD_W, BAND_Y - 0.6)).difference(pin_ko)
    for r, w in zip((38, 40, 42, 44, 46), (0.48, 0.42, 0.36, 0.29, 0.22)):
        for pts in shapely_lines(circle(SPR, r).exterior.intersection(upper)): gold("F.Cu", "F.Mask", pts, w)
    for r in (37, 39, 41, 43, 45):
        for pts in shapely_lines(circle(SPR, r).exterior.intersection(upper)): polyline("F.Cu", pts, 0.15)

    # ---- name band
    gx = jx(42.0) + 2.4
    name = text(gx, 45.4, "GHANEM", 3.35, track=1.5)
    sub = text(jx(47.6) + 2.4, 48.8, "ENGINEER", 1.15, track=0.9)
    serial = text(81.6, 48.9, "GG-2027-002 · REV A", 0.8, "end", 0.25)
    gold("F.Cu", "F.Mask", [(jx(BAND_Y) + 0.6, BAND_Y), (EDGE_X - 0.5, BAND_Y)], 0.13)
    gold_text("F.Cu", "F.Mask", name, 0.37); gold_text("F.Cu", "F.Mask", sub, 0.15); gold_text("F.Cu", "F.Mask", serial, 0.12)
    ko = Polygon()
    for grp, m in ((name, 0.7), (sub, 0.5), (serial, 0.5)):
        xs = [p[0] for st in grp for p in st]; ys = [p[1] for st in grp for p in st]
        ko = ko.union(box(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m))
    ko = ko.union(box(MARKER[0] - 0.5, MARKER[1] - 0.5, MARKER[2] + 0.5, MARKER[3] + 0.5))
    for v in VIAS_FRONT_KEEPOUT: ko = ko.union(circle(v, 0.75, 16))
    lower = keep.intersection(box(0, BAND_Y + 0.8, CARD_W, CARD_H)).difference(ko)
    for r in range(38, 92, 2):
        for pts in shapely_lines(circle(SPR, r).exterior.intersection(lower)): polyline("F.Cu", pts, 0.15)

    # ---- light slot: bare FR-4 on both faces, a line of text on layer 2 that only shows against the light
    slot = LineString([pol(SLOT_R, SLOT_A[0] + (SLOT_A[1] - SLOT_A[0]) * i / 96) for i in range(97)]).buffer(SLOT_HW, 24)
    for m in ("F.Mask", "B.Mask"): poly(m, list(slot.exterior.coords)[:-1])
    for st in arc_text(SLOT_R - 0.6, -0.5, "AVAILABLE SEPT. 2027", 1.18, 0.18): polyline("In1.Cu", st, 0.17)

    # ---- via fence along the wavefront
    step = math.degrees(1.2 / FENCE_R)
    for i in range(int((SLOT_A[1] - SLOT_A[0]) / step) + 1): th_pad(pol(FENCE_R, SLOT_A[0] + i * step), 0.6, 0.3)

    # ---- locating pins come up through these
    for p in PINS: th_pad(p, PIN_PAD, PIN_DRILL)

    # ---- BGA land pattern with dog-bone fan-out
    bx, by = BGA
    for j in range(8):
        for i in range(8): smd_pad((bx - 3.5 + i, by - 3.5 + j), 0.5, 0.5, '"F.Cu" "F.Mask"')
    for j in range(7):
        for i in range(7):
            # lands in gold, vias under mask on both faces (so the fab plugs them). The gold neck of each dog-bone
            # stops at the via pad's edge: its mask opening (0.15 wide, round end) ends 0.395 from the via centre,
            # clear of the 0.60 pad, so no hole is left half open.
            land, via = (bx - 3.5 + i, by - 3.5 + j), (bx - 3.0 + i, by - 3.0 + j)
            k = 1.0 - 0.395 / math.hypot(0.5, 0.5)
            th_pad(via, 0.6, 0.3, tented=True)
            art_trace([land, via], 0.11, land, via, mask_pts=[land, (land[0] + 0.5 * k, land[1] + 0.5 * k)])
    for i in range(8):                                   # top row escapes to staggered vias
        x = bx - 3.5 + i; y = 6.3 if i % 2 == 0 else 5.5
        th_pad((x, y), 0.6, 0.3); art_trace([(x, by - 3.5), (x, y)], 0.13, (x, by - 3.5), (x, y))
    for m in range(4):                                   # left column drops through staggered vias
        y = by - 1.5 + m; vx = 71.6 if m % 2 == 0 else 70.4
        th_pad((vx, y), 0.6, 0.3); art_trace([(bx - 3.5, y), (vx, y)], 0.13, (bx - 3.5, y), (vx, y))
    for i, cy in enumerate(CAST_Y):                      # castellated half-holes on the free edge
        py = by - 3.5 + i; dy = py - cy
        th_pad((EDGE_X, cy), 1.3, 0.8, "roundrect", 2.2)      # 0.25 ring around the half-hole
        art_trace([(EDGE_X - 1.0, cy), (83.2, cy), (83.2 - abs(dy), py), (bx + 3.5, py)], 0.15, (EDGE_X, cy), (bx + 3.5, py))

    # ---- edge fingers (front), bus to the bottom row, length-tuning meanders to test points
    for j, fy in enumerate(FINGER_Y):
        smd_pad((FINGER_X, fy), 4.5, 0.8, '"F.Cu" "F.Mask"', "roundrect")
        if j < 8:
            px = bx + 3.5 - j
            art_trace([(81.5, fy), (px + 1.0, fy), (px, fy - 1.0), (px, by + 3.5)], 0.15, (FINGER_X, fy), (px, by + 3.5))
        else:
            tx = 70.4 if j % 2 == 0 else 71.8
            smd_pad((tx, fy), 1.0, 1.0, '"F.Cu" "F.Mask"')
            art_trace([(81.5, fy), (79.6, fy)] + meander(79.6, 74.0, fy)[1:] + [(tx, fy)], 0.13, (FINGER_X, fy), (tx, fy))

    # ---- fiducial
    disc("F.Cu", (83.6, 19.6), 0.5); disc("F.Mask", (83.6, 19.6), 1.2)

    # ---- silkscreen (front)
    m = 4.4
    for q in ([(bx - m, by - m + 0.8), (bx - m, by - m), (bx - m + 0.8, by - m)], [(bx + m - 0.8, by - m), (bx + m, by - m), (bx + m, by - m + 0.8)],
              [(bx + m, by + m - 0.8), (bx + m, by + m), (bx + m - 0.8, by + m)], [(bx - m + 0.8, by + m), (bx - m, by + m), (bx - m, by + m - 0.8)]):
        polyline("F.SilkS", q, 0.15)
    disc("F.SilkS", (bx - 5.0, by - 5.0), 0.25)
    for (x, y, s, a) in ((69.4, 8.6, "U2", "start"), (84.8, 22.2, "J1", "end"), (82.6, 4.8, "J2", "end"), (70.0, 32.0, "TP", "start")):
        for st in text(x, y, s, 1.0, a): polyline("F.SilkS", st, 0.15)

    # ---- layer marker: one numeral per copper layer in a bare window
    x0, y0, x1, y1 = MARKER
    for mk in ("F.Mask", "B.Mask"): poly(mk, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    for i, lay in enumerate(("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")):
        for st in text(x0 + 0.9 + i * 1.3, y1 - 0.3, str(i + 1), 0.8, "middle"): polyline(lay, st, 0.14)

    # =========================================================================== back face
    # fab notes on arcs between the ledge and the slot, readable from the back
    for i, s in enumerate(["GG-2027-002 · REV A", "FR-4 · 4 LAYERS · ENIG", "LAID OUT BY THE SAME PERSON,", "ETCHED IN SHENZHEN."]):
        gold_text("B.Cu", "B.Mask", back_arc_text(44.8 - i * 1.3, -0.5, s, 0.8, 0.18), 0.12)
    # inside the antenna
    xi = (COIL["x0"] + COIL["turns"] * COIL["pitch"] + COIL["x1"] - COIL["turns"] * COIL["pitch"]) / 2
    gold_text("B.Cu", "B.Mask", text(xi + 0.4, 21.6, "13.56 MHZ · TAP PHONE HERE", 0.85, track=0.2, rot=-90, mirror=True), 0.13)
    gold_text("B.Cu", "B.Mask", text(xi - 1.6, 21.6, "NO BATTERY ON THIS CARD", 0.68, track=0.12, rot=-90, mirror=True), 0.11)
    # coupon only, hidden under the ledge once assembled: text-height and line-width ladders
    a = -13.0
    for cap in (0.5, 0.6, 0.7, 0.8, 1.0):
        gold_text("B.Cu", "B.Mask", back_arc_text(37.2, a, f"{cap:.1f}", cap, 0.1), max(0.10, cap / 9), min_w=0.10); a += 3.2
    for i, w in enumerate((0.10, 0.127, 0.15, 0.20, 0.25)):
        gold("B.Cu", "B.Mask", [pol(37.0 + 1.6 * t / 8, 3.0 + i * 1.3) for t in range(9)], w, min_w=0.10)
    gold_text("B.Cu", "B.Mask", back_arc_text(37.2, 14.5, "REV A", 0.7, 0.15), 0.1)
    # vernier across the ledge's edge, read from the back: these ticks are 1.35 deg apart, the ones engraved on the
    # aluminium 1.50 deg apart; ten of these span nine of those, so one step of coincidence is 0.15 deg = 0.1 mm at R40
    for i in range(11):
        a = VERNIER_A0 + i * VERNIER_STEP_PCB
        gold("B.Cu", "B.Mask", [pol(R_JOINT + LEDGE + 0.5, a), pol(R_JOINT + LEDGE + 0.5 + (1.5 if i % 5 == 0 else 1.0), a)], 0.12)
    # silkscreen (back)
    for (x, y, s) in ((62.9, 42.35, "U1"), (62.4, 37.6, "D1"), (88.0, 0, "")):
        if s:
            for st in text(x, y, s, 1.0, "start", mirror=True): polyline("B.SilkS", st, 0.15)
    for st in text(79.0, 49.05, "ANT1", 1.0, "start", mirror=True): polyline("B.SilkS", st, 0.15)

    # ---- antenna as a net-tie footprint: 7-turn rectangular spiral on the back, far from the aluminium
    pts = coil.spiral(COIL["x0"], COIL["y0"], COIL["x1"], COIL["y1"], COIL["turns"], COIL["pitch"], end_y=COIL["end_y"]) + [COIL_END]
    L = coil.inductance(pts, COIL["w"])
    ant = [f'  (footprint "gg_card:ANT1_spiral_7T" (layer "B.Cu") (tstamp {uid()}) (at {OX} {OY})',
           '    (attr board_only exclude_from_pos_files exclude_from_bom)',
           f'    (fp_text reference "ANT1" (at 77.7 51.6) (layer "B.Fab") hide (effects (font (size 1 1) (thickness 0.15)) (justify mirror)) (tstamp {uid()}))',
           f'    (fp_text value "{L:.2f}uH_free_air_calc" (at 77.7 53.2) (layer "B.Fab") hide (effects (font (size 1 1) (thickness 0.15)) (justify mirror)) (tstamp {uid()}))',
           '    (net_tie_pad_groups "1, 2")']
    for p, q in zip(pts, pts[1:]):
        ant.append(f'    (fp_line (start {p[0]:.4f} {p[1]:.4f}) (end {q[0]:.4f} {q[1]:.4f}) (stroke (width {COIL["w"]}) (type solid)) (layer "B.Cu") (tstamp {uid()}))')
    # the whole antenna stays under mask: bare turns would be loaded by a finger and leave 0.15 mask webs
    ant.append(f'    (pad "1" smd circle (at {pts[0][0]:.4f} {pts[0][1]:.4f}) (size 0.2 0.2) (layers "B.Cu") (tstamp {uid()}))')
    ant.append(f'    (pad "2" smd circle (at {COIL_END[0]:.4f} {COIL_END[1]:.4f}) (size 0.2 0.2) (layers "B.Cu") (tstamp {uid()}))')
    ant.append('  )')

    # nets of the decorative islands (isolated pads keep no net)
    roots = {}
    for k in _parent:
        roots.setdefault(_find(k), []).append(k)
    netof = {}
    for root, members in roots.items():
        if len(members) > 1:
            n = len(NETS) + 1; NETS.append(f"ART_{n}")
            for mkey in members: netof[mkey] = n
    art = [f'  (footprint "gg_card:ART_front" (layer "F.Cu") (tstamp {uid()}) (at {OX} {OY})',
           '    (attr board_only exclude_from_pos_files exclude_from_bom)',
           f'    (fp_text reference "ART1" (at 60 -3) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp {uid()}))',
           f'    (fp_text value "decorative_pads_and_holes" (at 60 -1.5) (layer "F.Fab") hide (effects (font (size 1 1) (thickness 0.15))) (tstamp {uid()}))']
    for i, (k, body) in enumerate(ART_PADS):
        net = f' (net {netof[k]} "{NETS[netof[k] - 1]}")' if k in netof else ""
        art.append(f'    (pad "{i + 1}" {body}{net} (tstamp {uid()}))')
    art.append('  )')
    for k, pts, w in ART_TRACKS:
        for p, q in zip(pts, pts[1:]):
            OUT.append(f'  (segment (start {P(p)}) (end {P(q)}) (width {w}) (layer "F.Cu") (net {netof[k]}) (tstamp {uid()}))')
    return art, ant, L

NETS = []

# vias of the tag circuit come through to the front; keep the relief rings off them (positions from place_parts.py)
VIAS_FRONT_KEEPOUT = [COIL_END, (69.9, 40.2), (69.0, 39.4), (63.6, 39.4)]

HEADER = '''(kicad_pcb (version 20221018) (generator gg_card_gen)
  (general (thickness %s))
  (paper "A4")
  (title_block (title "Hybrid card - PCB half") (rev "A") (company "Gabriel Ghanem") (comment 1 "First article / test coupon"))
  (layers
    (0 "F.Cu" signal) (1 "In1.Cu" signal) (2 "In2.Cu" signal) (31 "B.Cu" signal)
    (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user) (39 "F.Mask" user) (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments")
    (44 "Edge.Cuts" user) (45 "Margin" user) (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user) (49 "F.Fab" user))
  (setup
    (stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.21) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.0175))
      (layer "dielectric 2" (type "core") (thickness %s) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.0175))
      (layer "dielectric 3" (type "prepreg") (thickness 0.21) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
      (castellated_pads yes))
    (pad_to_mask_clearance 0) (aux_axis_origin %s %s) (grid_origin %s %s))
  (net 0 "")
''' % (BOARD_T, round(BOARD_T - 2 * (0.035 + 0.0175 + 0.21), 4), OX, OY, OX, OY)

if __name__ == "__main__":
    art, ant, L = build()
    out = HERE / "out"; out.mkdir(exist_ok=True)
    nets = "".join(f'  (net {i + 1} "{n}")\n' for i, n in enumerate(NETS))
    (out / "stage1.kicad_pcb").write_text(HEADER + nets + "\n".join(art) + "\n" + "\n".join(ant) + "\n" + "\n".join(OUT) + "\n)\n", encoding="utf-8")
    print(f"stage 1 written: {len(OUT)} items, {len(ART_PADS)} art pads, {len(NETS)} decorative nets, antenna {L:.2f} uH (free air, calculated)")
    print("board bbox", [round(v, 2) for v in BOARD.bounds], "area mm2", round(BOARD.area, 1))
