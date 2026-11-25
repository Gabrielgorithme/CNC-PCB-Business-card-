"""Concept B2 rev 2 - WAVEFRONT. The aluminium holds the board on three sides: the wavefront joint (R36 = 18th ripple crest)
plus a rim along the top and bottom edges. The rim is 3.18 mm, the card's corner radius, so it ends square on the right
edge instead of in a feather; the board shows on 88 % of that edge. One 1.2 mm four-layer board sits on a 0.5 mm ledge
(4 mm along the joint, 1.5 mm under the rims) and is located by two pins milled from the solid."""
from lib import *

URL = "https://gabrielgorithme.github.io/CNC-Business-card-/"
SPR = (190, 215)
RJ, LEDGE, RIM, RLEDGE = 360, 40, 32, 15
BAND = 384
SLOT_R, SLOT_HW, SLOT_A = 480, 13, (-18, 17)
FENCE_R = 506
PINS = [(SPR[0] + 380 * math.cos(math.radians(a)), SPR[1] + 380 * math.sin(math.radians(a))) for a in (-24, 22)]
BGA = (764, 112)
FINGER_Y = [232 + j * 12 for j in range(12)]
CAST_Y = [56 + i * 16 for i in range(8)]
jx = lambda y, r=RJ: SPR[0] + math.sqrt(r * r - (y - SPR[1]) ** 2)      # joint abscissa at height y

def _board(inset_arc=0, inset_rim=0):
    g = box(SPR[0], RIM + inset_rim, W + 200, H - RIM - inset_rim).difference(circle(*SPR, RJ + inset_arc))
    return g.buffer(-10, 16).buffer(10, 16).intersection(CARD)

def regions():
    pcb = _board()
    return CARD.difference(pcb), pcb

def slot_geom():
    return LineString(arc_pts(*SPR, SLOT_R, *SLOT_A)).buffer(SLOT_HW, 16)

def slot_ink(col):
    return arc_text(*SPR, SLOT_R - 6, -0.5, "AVAILABLE SEPT. 2027", 1.18, col, 0.18, wt=1.7)

def fence():
    step = math.degrees(12 / FENCE_R)
    n = int((SLOT_A[1] - SLOT_A[0]) / step)
    return [(SPR[0] + FENCE_R * math.cos(math.radians(SLOT_A[0] + i * step)), SPR[1] + FENCE_R * math.sin(math.radians(SLOT_A[0] + i * step))) for i in range(n + 1)]

def bga_pads():
    return [(BGA[0] - 35 + i * 10, BGA[1] - 35 + j * 10) for j in range(8) for i in range(8)]

def bga_vias():
    return [(BGA[0] - 30 + i * 10, BGA[1] - 30 + j * 10) for j in range(7) for i in range(7)]

def top_vias():
    return [(BGA[0] - 35 + i * 10, 63 if i % 2 == 0 else 55) for i in range(8)]

def left_vias():
    return [(716 if m % 2 == 0 else 704, BGA[1] - 15 + m * 10) for m in range(4)]

def meander(x0, x1, y, amp=3.6, period=7.0):
    pts = [(x0, y)]; x = x0; up = True
    while x + period <= x1:
        pts += [(x, y - amp if up else y + amp), (x + period / 2, y - amp if up else y + amp), (x + period / 2, y)]
        x += period / 2; up = not up
    pts.append((x1, y))
    return pts

def layer_marker(x, y, backlit=False):
    g = rrect(x, y, x + 56, y + 14, 3)
    def ink(col): return "".join(T(x + 8 + i * 13, y + 11, str(i + 1), 0.8, col, "middle", wt=1.4) for i in range(1, 4))
    return window(g, ink, backlit=backlit) + T(x + 8, y + 11, "1", 0.8, "#170a00" if backlit else GOLD, "middle", wt=1.4)

def recto(backlit=False):
    alu, pcb = regions()
    cx, cy = SPR
    slot = slot_geom()
    b = []
    pin_ko = circle(*PINS[0], 20).union(circle(*PINS[1], 20))
    name_ko = box(500, 414, 762, 462).union(box(452, 470, 640, 494)).union(box(640, 474, 832, 494)).union(box(770, 390, 838, 416))
    zone = pcb.difference(pin_ko).difference(box(0, BAND - 6, W, H))
    b.append(rings(cx, cy, zone, 370, 460, offset=10, kind="relief"))
    b.append(rings(cx, cy, zone, 380, 460, w0=4.8, w1=2.2))
    b.append(rings(cx, cy, pcb.intersection(box(0, BAND + 8, W, H)).difference(name_ko), 380, 900, kind="relief"))
    if not backlit: b.append(window(slot, slot_ink))
    fv = fence(); b += [via(x, y, 1.8, 4.2) for x, y in fv]
    for x, y in PINS: b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{GOLDF}"/>')
    # --- BGA land pattern with dog-bone fan-out
    bx, by = BGA
    for (px, py), (vx, vy) in zip([(bx - 35 + i * 10, by - 35 + j * 10) for j in range(7) for i in range(7)], bga_vias()):
        b.append(P(f"M{px},{py} L{vx},{vy}", 1.1, GOLD))
    b += [f'<circle cx="{x}" cy="{y}" r="2.5" fill="{GOLDF}"/>' for x, y in bga_pads()]
    b += [via(x, y, 0.9, 2.0) for x, y in bga_vias()]
    # top row escapes upward to staggered vias (inner layers)
    for x, y in top_vias(): b.append(P(f"M{x},{by-35} V{y}", 1.3, GOLD)); b.append(via(x, y, 1.4, 3.4))
    # castellated half-holes on the right edge, into the right column
    for i, cyy in enumerate(CAST_Y):
        py = by - 35 + i * 10; dy = py - cyy
        b.append(P(f"M846,{cyy} H832 L{832-abs(dy)},{py} H{bx+35}", 1.5, GOLD))
        b.append(f'<rect x="842" y="{cyy-5.5}" width="20" height="11" rx="2" fill="{GOLDF}"/><circle cx="{W}" cy="{cyy}" r="4.2" fill="#050506"/>')
    # edge fingers: 0-7 to the bottom row, 8-11 through length-tuning meanders to test points
    for j, fy in enumerate(FINGER_Y):
        b.append(f'<rect x="808" y="{fy-4}" width="60" height="8" rx="4" fill="{GOLDF}"/>')
        if j < 8:
            px = bx + 35 - j * 10
            b.append(P(f"M808,{fy} H{px+10} L{px},{fy-10} V{by+35}", 1.5, GOLD))
        else:
            tx = 704 if j % 2 == 0 else 718
            b.append(P(pl([(808, fy), (796, fy)] + [(796 - (x - 740), y) for x, y in meander(740, 796, fy)][1:] + [(tx, fy)]), 1.3, GOLD))
            b.append(f'<circle cx="{tx}" cy="{fy}" r="5" fill="{GOLDF}"/>')
    for (vx, vy) in left_vias():
        b.append(P(f"M{bx-35},{vy} H{vx}", 1.3, GOLD)); b.append(via(vx, vy, 1.4, 3.4))
    # silkscreen
    b.append(P(f"M{bx-44},{by-36} V{by-44} H{bx-36} M{bx+36},{by-44} H{bx+44} V{by-36} M{bx+44},{by+36} V{by+44} H{bx+36} M{bx-36},{by+44} H{bx-44} V{by+36}", 1.5, SILK))
    b.append(f'<circle cx="{bx-50}" cy="{by-50}" r="2.4" fill="{SILK}"/>')
    b.append(T(696, 86, "U2", 1.0, SILK)); b.append(T(848, 222, "J1", 1.0, SILK, "end")); b.append(T(826, 48, "J2", 1.0, SILK, "end"))
    b.append(T(700, 320, "TP", 1.0, SILK))
    b.append(fiducial(836, 196))
    if not backlit: b.append(layer_marker(776, 396))
    # name band
    b.append(P(f"M{jx(BAND):.1f},{BAND} H{W}", 1.3, GOLD))
    b.append(T(jx(420) + 24, 454, "GHANEM", 3.35, GOLD, "start", 1.5))
    b.append(T(jx(476) + 24, 488, "ENGINEER", 1.15, GOLD, "start", 0.9))
    b.append(T(W - 40, 489, "GG-2027-002 · REV B", 0.8, GOLD, "end", 0.25))
    # --- aluminium: nothing engraved on the wavy part
    a = [spring(cx, cy, 1, "GG"), hole(50, 50)]
    a.append(P(f"M0,{BAND} H{jx(BAND):.1f}", 1.2, "#5d646c"))
    a.append(T(jx(454) - 24, 454, "GABRIEL", 3.35, ENG, "end", 1.5))
    a.append(T(jx(488) - 24, 488, "MANUFACTURING", 1.15, ENG, "end", 0.9))
    top = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="#d5d8dc" stroke="#30353a" stroke-width="1.2"/><circle cx="{x-1.5:.1f}" cy="{y-1.5:.1f}" r="6" fill="#eef0f2" opacity=".7"/>' for x, y in PINS)
    lit = None
    if backlit:
        e = arc_pts(cx, cy, SLOT_R, SLOT_A[1], SLOT_A[1], 1)[0]
        lit = window(slot, slot_ink, backlit=True, led=(e[0], e[1], 90)) + layer_marker(776, 396, True)
        glow = lambda x, y, r: f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*5:.1f}" fill="url(#star)"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{r*0.9:.1f}" fill="#fffbe8"/>'
        lit += "".join(glow(x, y, 1.8) for x, y in fv) + "".join(glow(x, y, 1.0) for x, y in bga_vias())
        lit += "".join(glow(x, y, 1.4) for x, y in left_vias() + top_vias())
    def rim_ripple(x, y):          # ripples everywhere on the aluminium except the name band (the bottom rim stays flat with it)
        return ripple(cx / 10, cy / 10, BAND / 10)(x, y)
    return card(alu_image(rim_ripple), alu, pcb, "\n".join(b), "\n".join(a), backlit=lit, extra_top=top)

def verso():
    pcb = mirror(_board(LEDGE, RLEDGE))            # what shows; the ledge hides the rest of the board
    alu = CARD.difference(pcb)
    sx, sy = W - SPR[0], SPR[1]
    RL = RJ + LEDGE
    M = lambda x: W - x
    # =============== PCB (left), 0.5 mm below the aluminium
    b = []
    b.append(window(mirror(slot_geom()), lambda col: f'<g transform="translate({W},0) scale(-1,1)">{slot_ink(col)}</g>'))
    b += [via(M(x), y, 1.8, 4.2) for x, y in fence()]
    b.append(rings(sx, sy, pcb.difference(box(0, BAND - 6, W, H)), RL + 20, 460, kind="relief"))
    b += [via(M(x), y, 0.9, 2.2) for x, y in bga_vias()]
    b += [via(M(x), y, 1.4, 3.4) for x, y in left_vias() + top_vias()]
    for cyy in CAST_Y: b.append(f'<rect x="-6" y="{cyy-5.5}" width="20" height="11" rx="2" fill="{GOLDF}"/><circle cx="0" cy="{cyy}" r="4.2" fill="#050506"/>')
    for fy in FINGER_Y: b.append(f'<rect x="-12" y="{fy-4}" width="60" height="8" rx="4" fill="{GOLDF}"/>')
    b.append(T(8, 222, "J1", 1.0, SILK)); b.append(T(22, 74, "J2", 1.0, SILK))
    notes = ["GG-2027-002 · REV B", "FR-4 · 4 LAYERS · 1.20", "ENIG · BLACK MASK", "LAID OUT BY THE SAME", "PERSON, ETCHED IN", "SHENZHEN."]
    b.append(f'<g transform="translate(70,352) rotate(-90)">' + "".join(T(0, i * 15, ln, 0.78, GOLD, "start", 0.18, wt=1.1) for i, ln in enumerate(notes)) + "</g>")
    b.append(rect_coil(30, 398, 290, 486, 4, r=16))
    b.append(T(160, 440, "13.56 MHZ · TAP HERE", 0.9, GOLD, "middle", 0.25))
    b.append(T(160, 458, "NO BATTERY ON THIS CARD", 0.72, GOLD, "middle", 0.15, wt=1.0))
    e = arc_pts(*SPR, SLOT_R, SLOT_A[1], SLOT_A[1], 1)[0]; d1 = (M(e[0]), e[1] + 23)
    u1, c1 = (158, d1[1]), (126, d1[1])
    b.append(P(f"M{u1[0]},{u1[1]+8} V398 M{u1[0]-8},{u1[1]} H{c1[0]+6} M{u1[0]+8},{u1[1]} H{d1[0]-7}", 2.0, GOLD))
    b.append(smd(*u1, 16, 16)); b.append(smd(*c1, 10, 5)); b.append(smd(*d1, 10, 5, body="#e8e2c4"))
    b.append(T(u1[0] + 14, u1[1] + 17, "U1", 0.95, SILK)); b.append(T(c1[0] - 12, c1[1] + 4, "C1", 0.95, SILK, "end")); b.append(T(d1[0] + 12, d1[1] + 4, "D1", 0.95, SILK))
    b.append(T(298, 478, "ANT1", 0.95, SILK))
    b.append(fiducial(M(836), 196))
    b.append(f'<path d="{path(pcb.exterior)}" fill="none" stroke="#000" stroke-width="30" opacity=".6" filter="url(#soft)"/>')
    # =============== aluminium: a full drawing sheet
    a = [spring(sx, sy, -1), hole(W - 50, 50)]
    a.append(P(f"M{sx-148},{sy} H{sx+148} M{sx},{sy-148} V{sy+148}", 1, ENG2, extra='stroke-dasharray="16 4 3 4"'))
    # inch rule along the top edge, mm rule along the bottom edge
    for i in range(0, 54):
        x = i * 15.875; hh = 15 if i % 16 == 0 else 11 if i % 8 == 0 else 8 if i % 4 == 0 else 6 if i % 2 == 0 else 4
        if 34 < x < W - 34: a.append(P(f"M{x:.1f},0 v{hh}", 1, ENG))
        if i % 16 == 0 and 0 < i < 50: a.append(T(x + 3, 27, str(i // 16), 0.66, ENG))
    a.append(T(44, 28, "IN", 0.6, ENG2)); a.append(ruler(0, W, ENG)); a.append(T(44, H - 20, "MM", 0.6, ENG2))
    a.append(T(70, 43, "IF YOU CAN READ THIS, THE ENGRAVING BIT WAS SHARP", 0.7, ENG2, "start", 0.1, wt=1.0))
    # flatness of the common face + datum A, material
    s, w_ = fcf(318, 54, "flatness", "0.05"); a.append(s)
    a.append(P(f"M{318+w_},66 h8", 1.3) + P(f"M{326+w_},59 v14 l11,-7 z", 1, fill=ENG))
    a.append(f'<rect x="{337+w_}" y="55" width="22" height="22" fill="none" stroke="{ENG}" stroke-width="1.4"/>' + T(348 + w_, 72, "A", 1.1, ENG, "middle"))
    a.append(T(318, 100, "AL 7075-T6 + FR-4", 0.72, ENG, "start", 0.15))
    # flexure note
    a.append(T(452, 57, "3× FLEXURE LEG", 1.05, ENG, "start", 0.35)); a.append(T(452, 74, "WEB 0.40 ±0.02", 1.1, ENG))
    s, w_ = fcf(452, 80, "profile", "0.05", ("A",)); a.append(s)
    a.append(P(f"M{452+w_},{92} h10 L{sx-28},{sy-92}", 1.2)); a.append(f'<circle cx="{sx-28}" cy="{sy-92}" r="3" fill="{ENG}"/>')
    # hole note
    hx, hy = W - 50, 50
    a.append(P(f"M{hx-24},{hy} h48 M{hx},{hy-24} v48", .9, ENG2, extra='stroke-dasharray="9 3 2 3"'))
    a.append(T(hx - 40, 47, "Ø3 D11", 1.1, ENG, "end")); a.append(P(f"M{hx-36},{43} h8", 1.2)); a.append(arrow(hx - 16, 46, 14))
    s, w_ = fcf(0, 0, "position", "Ø0.05", ("A", "B", "C")); a.append(f'<g transform="translate(650,54) scale(.85)">{s}</g>')
    # datums B (long edge) and C (short edge)
    a.append(P(f"M523,{H} h14 l-7,-11 z", 1, fill=ENG) + P(f"M530,{H-11} v-13") + f'<rect x="519" y="{H-46}" width="22" height="22" fill="none" stroke="{ENG}" stroke-width="1.4"/>' + T(530, H - 29, "B", 1.1, ENG, "middle"))
    a.append(P(f"M{W},93 v14 l-11,-7 z", 1, fill=ENG) + P(f"M{W-11},100 h-13") + f'<rect x="{W-46}" y="89" width="22" height="22" fill="none" stroke="{ENG}" stroke-width="1.4"/>' + T(W - 35, 106, "C", 1.1, ENG, "middle"))
    # QR, centred between the joint and the flexure
    q, n = qr(URL, 306, 128, 174, "alu"); a.append(q)
    a.append(T(302, 333, "SCAN · CAD · TOOLPATHS · VIDEO", 0.7, ENG, "start", 0.14))
    # Ø26 note
    a.append(P(f"M{sx-65},{sy+113} L{sx-72},{sy+140} H{sx-168}", 1.2)); a.append(arrow(sx - 65, sy + 113, -104))
    a.append(T(sx - 74, sy + 135, "Ø26 ±0.05", 1.1, ENG, "end"))
    # joint notes + vernier (1.50 deg engraved against 1.35 deg etched = 0.1 mm at the joint)
    a.append(T(306, 349, "JOINT R36 = 18TH RIPPLE", 0.7, ENG, "start", 0.14)); a.append(T(308, 363, "LEDGE 4 × 0.50 ±0.02", 0.7, ENG, "start", 0.14))
    va = 154.0; top = ""
    for i in range(11):
        A = math.radians(va - i * 1.5); L = 20 if i % 5 == 0 else 12
        a.append(P(f"M{sx+(RL-4)*math.cos(A):.1f},{sy+(RL-4)*math.sin(A):.1f} L{sx+(RL-4-L)*math.cos(A):.1f},{sy+(RL-4-L)*math.sin(A):.1f}", 1.1, ENG))
        B = math.radians(va - i * 1.35)
        top += P(f"M{sx+(RL+5)*math.cos(B):.1f},{sy+(RL+5)*math.sin(B):.1f} L{sx+(RL+5+L)*math.cos(B):.1f},{sy+(RL+5+L)*math.sin(B):.1f}", 1.2, GOLD)
    a.append(arc_text(sx, sy, RL - 30, 146.5, "VERNIER 0.1 MM", 0.66, ENG2, 0.12, wt=1.0, inward=True))
    # G-code excerpt
    for i, ln in enumerate(["O2027 (GG CARD OP2)", "G21 G90 G17 G54", "T405 M6 (D1 2FL)", "S24000 M3", "G0 X26.6 Y15.8", "G1 Z-1.25 F120", "G3 X38.4 Y22. I-6.1", "   J9.4 F480", "(... 2847 BLOCKS)"]):
        a.append(T(402, 380 + i * 12.4, ln, 0.67, ENG, "start", 0.05, wt=1.0))
    # scallop comparator
    x0, y0, sw = 566, 386, 40
    a.append(T(x0, y0 - 8, "SCALLOP COMPARATOR · R1.5 BALL", 0.66, ENG, "start", 0.08, wt=1.0))
    for i, (step, hgt) in enumerate([("0.30", "7.5"), ("0.15", "1.9"), ("0.05", "0.2")]):
        xx = x0 + i * (sw + 16)
        a.append(f'<rect x="{xx}" y="{y0}" width="{sw}" height="{sw}" fill="#b9bdc3" stroke="{ENG}" stroke-width="1.2"/>')
        pitch = float(step) * 10; k = 0
        while k * pitch < sw - .5:
            a.append(P(f"M{xx + k*pitch + pitch/2:.2f},{y0+1} v{sw-2}", max(.35, pitch * .42), "#7b828a", extra='opacity=".85"')); k += 1
        a.append(T(xx + sw / 2, y0 + sw + 11, "S " + step, 0.68, ENG, "middle", 0.08, wt=1.0)); a.append(T(xx + sw / 2, y0 + sw + 22, hgt + " UM", 0.62, ENG2, "middle", 0.05, wt=1.0))
    # first-angle projection symbol + standards
    px, py = 736, 394
    a.append(P(f"M{px},{py} l22,-5 v22 l-22,-5 z", 1.2)); a.append(f'<circle cx="{px+42}" cy="{py+6}" r="11" fill="none" stroke="{ENG}" stroke-width="1.2"/><circle cx="{px+42}" cy="{py+6}" r="6" fill="none" stroke="{ENG}" stroke-width="1.2"/>')
    a.append(P(f"M{px-5},{py+6} h64", .8, ENG2, extra='stroke-dasharray="9 3 2 3"'))
    a.append(T(px, 432, "ISO 8015", 0.68, ENG, "start", 0.1, wt=1.0)); a.append(T(px, 445, "2768-FH", 0.68, ENG, "start", 0.1, wt=1.0))
    # title block
    a.append(f'<rect x="560" y="456" width="244" height="38" fill="none" stroke="{ENG}" stroke-width="1.3"/>' + P("M560,476 H804", 1.0))
    a.append(T(566, 471, "AVAILABLE SEPT. 2027", 1.0, ENG, "start", 0.25)); a.append(T(566, 489, "GABRIEL.GHANEM@GMAIL.COM", 0.8, ENG, "start", 0.15))
    # statement, set along the short edge
    a.append(f'<g transform="translate(826,474) rotate(-90)">' + T(0, 0, "DESIGNED, PROGRAMMED AND MACHINED BY", 0.8, ENG, "start", 0.2) + T(0, 16, "THE PERSON WHO HANDED IT TO YOU.", 0.8, ENG, "start", 0.2) + "</g>")
    return card(alu_image(None, seed=7), alu, pcb, "\n".join(b), "\n".join(a), extra_top=top)
