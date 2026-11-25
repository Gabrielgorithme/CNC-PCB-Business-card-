"""Concept B - BEZEL. The aluminium wraps the PCB. The joint is an arc concentric with the ripples (a wavefront).
One 1.2 mm four-layer board sits on a 0.5 mm ledge: flush on the recto, recessed on the verso where the parts hide.
A 1 mm slit through the rim keeps the frame from acting as a shorted turn around the NFC antenna."""
import numpy as np
from lib import *

URL = "https://gabrielgorithme.github.io/CNC-Business-card-/"
SPR = (215, 215)
RJ = 300                                   # joint radius = 15th ripple crest
WIN = (566, 60, 796, 146)                  # hidden-layer window (recto coordinates)
SLIT_X = 470

def regions():
    pcb = rrect(215, 30, 826, 510, 15).difference(circle(*SPR, RJ))
    pcb = rounded(pcb, 10)
    slit = box(SLIT_X - 5, -5, SLIT_X + 5, 32)
    alu = CARD.difference(pcb).difference(slit)
    return alu, pcb, slit

def rocket(x0, y0, sx=0.98, sy=1.55, flip=1):
    """Hull on the outer layer (gold in daylight); bulkheads, motor, recovery bay, avionics, payload on the inner layers."""
    tr = f'translate({x0},{y0}) scale({sx*flip},{sy})'
    hull = "M230,0 c-14,-9 -30,-13 -46,-13 h-150 l-18,-12 v12 h-8 v26 h8 v12 l18,-12 h150 c16,0 32,-4 46,-13 z"
    def inner(col):
        o = [f'<g transform="{tr}">']
        o.append(f'<path d="{hull}" fill="none" stroke="{col}" stroke-width="2.2"/>')
        o.append(f'<path d="M16,-25 l18,12 v-12 z M16,25 l18,-12 v12 z" fill="{col}"/>')                       # fins
        o.append(f'<path d="M8,-6 h-12 l-6,-5 v22 l6,-5 h12 z" fill="{col}"/>')                                  # nozzle
        o.append(f'<rect x="14" y="-9" width="58" height="18" rx="2" fill="{col}"/>')                           # motor grain
        for x in (78, 112, 148, 184): o.append(f'<path d="M{x},-13 v26" stroke="{col}" stroke-width="1.6"/>')   # bulkheads
        o.append(f'<path d="M82,-8 q4,8 8,0 t8,0 t8,0 M82,6 q4,-8 8,0 t8,0 t8,0" fill="none" stroke="{col}" stroke-width="1.3"/>')   # folded chute
        o.append(f'<rect x="118" y="-3" width="26" height="6" fill="{col}"/>' + "".join(f'<rect x="{119+i*5}" y="{-9 if i%2 else 5}" width="3.4" height="4" fill="{col}"/>' for i in range(5)))  # avionics
        o.append(f'<rect x="156" y="-8" width="16" height="16" fill="none" stroke="{col}" stroke-width="1.6"/><path d="M160,-4 h8 v8 h-8 z" fill="{col}"/>')  # payload
        o.append(f'<path d="M190,-9 q14,2 28,9 q-14,7 -28,9" fill="none" stroke="{col}" stroke-width="1.2"/>')  # nose rib
        o.append('</g>')
        return "".join(o)
    outer = f'<g transform="{tr}"><path d="{hull}" fill="none" stroke="{GOLD}" stroke-width="1.6"/></g>'
    return inner, outer

def stars(pcb, win, keep_out, n=26, seed=11):
    rng = np.random.default_rng(seed); out = []
    ok = pcb.buffer(-14).difference(win.buffer(16)).difference(keep_out)
    while len(out) < n:
        x, y = rng.uniform(300, 830), rng.uniform(30, 510)
        if ok.contains(Point(x, y)) and math.hypot(x - SPR[0], y - SPR[1]) > 482 and all(math.hypot(x - a, y - b) > 22 for a, b, _ in out):
            out.append((x, y, rng.choice([1.5, 1.5, 2.0, 2.0, 3.0])))
    return out

def recto(backlit=False):
    alu, pcb, slit = regions()
    cx, cy = SPR
    win = rrect(*WIN, 12)
    name_box = box(520, 386, 826, 510)
    label_box = box(WIN[2] - 150, WIN[3] + 6, WIN[2] + 6, WIN[3] + 28)
    allowed = pcb.difference(win.buffer(12)).difference(name_box).difference(label_box)
    b = []
    b.append(rings(cx, cy, allowed, RJ + 10, 900, offset=10, kind="relief"))
    b.append(rings(cx, cy, allowed, RJ + 20, 540, w0=4.8, w1=1.3))
    b.append(rings(cx, cy, allowed, 560, 900, kind="relief"))
    st = []
    inner, outer = rocket(WIN[0] + 4, (WIN[1] + WIN[3]) / 2)
    if not backlit: b.append(window(win, inner)); b.append(outer)
    b.append(T(WIN[2], WIN[3] + 20, "HOLD TO THE LIGHT", 0.8, GOLD, "end", 0.25))
    b.append(T(804, 424, "GABRIEL", 3.0, GOLD, "end", 1.3)); b.append(T(804, 466, "GHANEM", 3.0, GOLD, "end", 1.3))
    b.append(T(804, 492, "MANUFACTURING ENGINEER", 0.95, GOLD, "end", 0.42))
    a = [spring(cx, cy, 1, "GG"), hole(50, 50)]
    lit = None
    if backlit:
        lit = window(win, inner, backlit=True, led=(WIN[0] + 6, (WIN[1] + WIN[3]) / 2, 52))
        lit += "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*5:.1f}" fill="url(#star)"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{r*0.9:.1f}" fill="#fffbe8"/>' for x, y, r in st)
    top = f'<path d="{path(slit.intersection(CARD))}" fill="#050506"/>'
    return card(alu_image(ripple(cx / 10, cy / 10)), alu, pcb, "\n".join(b), "\n".join(a), backlit=lit, extra_top=top)

def verso():
    alu_r, pcb_r, slit_r = regions()
    pcb = mirror(pcb_r.buffer(-15))                       # what shows through the frame; the ledge hides the rest
    slit = mirror(box(SLIT_X - 5, -5, SLIT_X + 5, 47))
    alu = CARD.difference(pcb).difference(slit)
    sx, sy = W - SPR[0], SPR[1]
    wx0, wx1 = W - WIN[2], W - WIN[0]
    win = rrect(wx0, WIN[1], wx1, WIN[3], 12)
    inner, outer = rocket(wx1 - 4, (WIN[1] + WIN[3]) / 2, flip=-1)
    b = [window(win, inner)]
    b.append(T(64, 178, "13.56 MHZ · TAP OR SCAN", 0.95, GOLD, "start", 0.3))
    cx0, cy0, cx1, cy1 = 62, 196, 308, 442
    b.append(rect_coil(cx0, cy0, cx1, cy1, 6))
    q, n = qr(URL, 119, 253, 132, "white"); b.append(q)
    u1, c1, d1 = (352, 424), (382, 424), (wx1 + 14, (WIN[1] + WIN[3]) / 2)
    b.append(P(f"M{cx1},{360} H{u1[0]} V{u1[1]-8} M{u1[0]+8},{u1[1]} H{c1[0]-6} M{u1[0]-8},{u1[1]} H{320} V{d1[1]+22} H{d1[0]} V{d1[1]+7}", 2.2, GOLD))
    b.append(P(f"M{d1[0]},{d1[1]-7} V{d1[1]-26} H{d1[0]-40}", 2.2, GOLD)); b.append(via(d1[0] - 40, d1[1] - 26, 2, 4.5))
    b.append(smd(*u1, 16, 16, "U1", ly=24)); b.append(smd(*c1, 10, 5, "C1", ly=24)); b.append(smd(*d1, 10, 5, None, body="#e8e2c4", rot=90))
    b.append(T(62, 472, "NO BATTERY ON THIS CARD.", 0.8, GOLD, "start", 0.22)); b.append(T(62, 487, "YOUR PHONE POWERS THE LED.", 0.8, GOLD, "start", 0.22))
    edge = path(pcb.exterior)
    b.append(f'<path d="{edge}" fill="none" stroke="#000" stroke-width="26" opacity=".55" filter="url(#soft)"/>')
    a = [spring(sx, sy, -1), hole(W - 50, 50)]
    a.append(P(f"M{sx-148},{sy} H{sx+148} M{sx},{sy-148} V{sy+148}", 1, ENG2, extra='stroke-dasharray="16 4 3 4"'))
    a.append(T(478, 36, "3× FLEXURE LEG", 1.05, ENG, "start", 0.35)); a.append(T(478, 54, "WEB 0.40 ±0.02", 1.1, ENG))
    s, w_ = fcf(478, 62, "profile", "0.05", ("A",)); a.append(s)
    a.append(P(f"M{612},{48} h14 L{sx+6},{sy-96}", 1.2)); a.append(f'<circle cx="{sx+6}" cy="{sy-96}" r="3" fill="{ENG}"/>')
    a.append(P(f"M{sx-40},{sy+124} L{sx-52},{sy+158} H{sx+56}", 1.2)); a.append(arrow(sx - 40, sy + 124, -71))
    a.append(T(sx - 44, sy + 153, "Ø26 ±0.05", 1.1))
    # frame callouts
    xs = W - SLIT_X
    a.append(P(f"M{xs+5},{40} l10,22 v8", 1.1)); a.append(arrow(xs + 5, 40, -114))
    for i, ln in enumerate(["SLIT 1.0", "OPENS THE", "EDDY LOOP"]): a.append(T(xs - 22, 86 + i * 14, ln, 0.8, ENG, "start", 0.22))
    a.append(T(402, 394, "JOINT R30 = 15TH RIPPLE · LEDGE 0.50 ±0.02 · PCB 1.20", 0.78, ENG2, "start", 0.2))
    for i, ln in enumerate(["DESIGNED, PROGRAMMED AND", "MACHINED BY THE PERSON", "WHO HANDED IT TO YOU."]):
        a.append(T(826, 420 + i * 18, ln, 1.1, ENG, "end", 0.3))
    a.append(T(826, 482, "GABRIEL.GHANEM@GMAIL.COM", 1.05, ENG, "end", 0.3)); a.append(T(826, 501, "AVAILABLE SEPT. 2027", 1.15, ENG, "end", 0.4))
    a.append(ruler(0, W, ENG))
    top = f'<path d="{path(slit.intersection(CARD))}" fill="#050506"/>'
    return card(alu_image(None, seed=7), alu, pcb, "\n".join(b), "\n".join(a), extra_top=top)
