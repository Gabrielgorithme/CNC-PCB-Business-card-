"""Concept C - ZIPPER. The two materials dissolve into each other through fifteen interleaved fingers,
so every ripple alternates milled / gold seven times on its way across. Banknote details on the PCB:
guilloche rosette, watermark window, ring of pinhole stars, microtext. One single 1.6 mm four-layer board."""
from lib import *

URL = "https://gabrielgorithme.github.io/CNC-Business-card-/"
SPR = (590, 220)                 # same place as on the first card
X0, X1, PITCH = 300, 440, 26     # comb zone and finger width (2.6 mm)
BAND, JB = 392, 370              # name band and the straight joint inside it
WM = (150, 200)                  # watermark window

def regions():
    alu = box(X1, -300, W + 300, BAND + 1).union(box(JB, BAND - 1, W + 300, H + 300))
    for i in range(1, 15, 2):
        alu = alu.union(box(X0, i * PITCH, X1 + 2, (i + 1) * PITCH))
    alu = rounded(alu, 11).intersection(CARD)
    return alu, CARD.difference(alu)

def rosette(cx, cy, r_mid=71, amp=11, lobes=14, n=6, col=GOLD, w=0.9):
    """Guilloche band: n phase-shifted epitrochoid-like loops. Historically cut on rose-engine lathes."""
    o = []
    for k in range(n):
        ph = 2 * math.pi * k / (n * lobes)
        pts = [(cx + (r_mid + amp * math.cos(lobes * t + ph * lobes)) * math.cos(t),
                cy + (r_mid + amp * math.cos(lobes * t + ph * lobes)) * math.sin(t)) for t in [2 * math.pi * i / 720 for i in range(721)]]
        o.append(P(pl(pts), w, col))
    return "".join(o)

def star_ring(cx, cy, r=93, n=16):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), 2.6 if i % 4 == 0 else 1.6) for i in range(n)]

def watermark(cx, cy):
    def g(col):
        o = [T(cx, cy + 20, "GG", 4.0, col, "middle", 0.9, wt=7)]
        o.append(f'<circle cx="{cx}" cy="{cy}" r="41" fill="none" stroke="{col}" stroke-width="1.6"/>')
        for i in range(48):
            a = 2 * math.pi * i / 48
            o.append(P(f"M{cx+44*math.cos(a):.1f},{cy+44*math.sin(a):.1f} L{cx+(50 if i%4 else 53)*math.cos(a):.1f},{cy+(50 if i%4 else 53)*math.sin(a):.1f}", 1.2, col))
        return "".join(o)
    return g

def recto(backlit=False):
    alu, pcb = regions()
    cx, cy = SPR
    win = circle(*WM, 52)
    allowed = pcb.difference(circle(*WM, 106)).difference(box(0, BAND - 8, JB + 60, H)).difference(box(0, 0, 34, H))
    b = []
    b.append(rings(cx, cy, allowed, 140, 900, offset=10, kind="relief"))
    b.append(rings(cx, cy, allowed, 140, 440, w0=4.6, w1=1.5))
    b.append(rings(cx, cy, allowed, 460, 900, kind="relief"))
    b.append(rosette(*WM))
    st = star_ring(*WM)
    b += [via(x, y, r, r + 2.0) for x, y, r in st]
    if not backlit: b.append(window(win, watermark(*WM)))
    b.append(P(f"M0,{BAND} H{JB}", 1.3, GOLD))
    b.append(T(JB - 24, 468, "GABRIEL", 3.35, GOLD, "end", 1.5))
    b.append(T(JB - 24, 505, "MANUFACTURING", 1.15, GOLD, "end", 0.9))
    b.append(f'<g transform="translate(22,{BAND-14}) rotate(-90)">' + T(0, 0, "IF YOU CAN READ THIS, THE ETCH WAS SHARP", 0.7, GOLD, "start", 0.2, wt=1.0) + "</g>")
    a = [spring(cx, cy, 1, "GG"), hole(W - 50, 50)]
    a.append(P(f"M{JB},{BAND} H{W}", 1.2, "#5d646c"))
    a.append(T(JB + 24, 468, "GHANEM", 3.35, ENG, "start", 1.5))
    a.append(T(JB + 24, 505, "ENGINEER", 1.15, ENG, "start", 0.9))
    a.append(T(W - 44, 505, "GG-2027-002 · REV A", 0.75, ENG2, "end", 0.25))
    lit = None
    if backlit:
        lit = window(win, watermark(*WM), backlit=True, led=(WM[0], WM[1] + 44, 64))
        lit += "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*5:.1f}" fill="url(#star)"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{r*0.9:.1f}" fill="#fffbe8"/>' for x, y, r in st)
    return card(alu_image(ripple(cx / 10, cy / 10, BAND / 10)), alu, pcb, "\n".join(b), "\n".join(a), backlit=lit)

def verso():
    alu, pcb = map(mirror, regions())
    sx, sy = W - SPR[0], SPR[1]
    wx, wy = W - WM[0], WM[1]
    jb = W - JB
    # ---------------- PCB (right)
    b = [rect_coil(578, 24, 836, 372, 4)]
    b.append(window(circle(wx, wy, 52), watermark(wx, wy)))
    b += [via(W - x, y, r, r + 2.0) for x, y, r in star_ring(*WM)]
    b.append(T(wx, 66, "13.56 MHZ · TAP HERE", 0.9, GOLD, "middle", 0.25)); b.append(T(wx, 84, "NO BATTERY ON THIS CARD", 0.72, GOLD, "middle", 0.15, wt=1.0))
    u1, c1, d1 = (wx + 20, 320), (wx + 52, 320), (wx - 14, wy + 66)
    b.append(P(f"M{600},{344} H{u1[0]-24} V{u1[1]} H{u1[0]-8} M{u1[0]+8},{u1[1]} H{c1[0]-6} M{u1[0]},{u1[1]-8} V{d1[1]} H{d1[0]+14}", 2.2, GOLD))
    b.append(smd(*u1, 16, 16, "U1", lx=4, ly=24)); b.append(smd(*c1, 10, 5, "C1", ly=24)); b.append(smd(*d1, 10, 5, None, body="#e8e2c4"))
    q, n = qr(URL, 716, 410, 106, "gold"); b.append(q)
    tx = jb + 40
    b.append(T(tx, 420, "AVAILABLE", 1.3, GOLD, "start", 0.5)); b.append(T(tx, 441, "SEPT. 2027", 1.3, GOLD, "start", 0.5))
    b.append(T(tx, 465, "GABRIEL.GHANEM", 0.95, GOLD, "start", 0.25)); b.append(T(tx, 480, "@GMAIL.COM", 0.95, GOLD, "start", 0.25))
    b.append(T(tx, 502, "LAID OUT BY HIM,", 0.7, GOLD, "start", 0.15, wt=1.0)); b.append(T(tx, 515, "ETCHED IN SHENZHEN.", 0.7, GOLD, "start", 0.15, wt=1.0))
    # ---------------- aluminium (left)
    a = [spring(sx, sy, -1), hole(50, 50)]
    a.append(P(f"M{sx-148},{sy} H{sx+148} M{sx},{sy-148} V{sy+148}", 1, ENG2, extra='stroke-dasharray="16 4 3 4"'))
    a.append(T(96, 34, "3× FLEXURE LEG", 1.05, ENG, "start", 0.35)); a.append(T(96, 52, "WEB 0.40 ±0.02", 1.1, ENG))
    s, w_ = fcf(282, 30, "profile", "0.05", ("A",)); a.append(s)
    a.append(P(f"M{320},{54} L{sx+44},{sy-100}", 1.2)); a.append(f'<circle cx="{sx+44}" cy="{sy-100}" r="3" fill="{ENG}"/>')
    a.append(P(f"M{sx-92},{sy+92} L{sx-138},{sy+142} H34", 1.2)); a.append(arrow(sx - 92, sy + 92, -47))
    a.append(T(36, sy + 136, "Ø26 ±0.05", 1.1))
    a.append(T(232, 370, "15× FINGER 2.6 · R1.1", 0.82, ENG, "start", 0.2)); a.append(T(232, 385, "GAP 0.05 MAX", 0.82, ENG, "start", 0.2))
    a.append(P(f"M{232+158},{366} H{406} L{426},{352}", 1.1)); a.append(arrow(426, 352, -35))
    # band: scallop comparator, statement, vernier at the straight joint
    x0, y0, sw = 40, 414, 50
    a.append(T(x0, y0 - 8, "SCALLOP COMPARATOR · R1.5 BALL", 0.7, ENG, "start", 0.12))
    for i, (step, hgt) in enumerate([("0.30", "7.5"), ("0.15", "1.9"), ("0.05", "0.2")]):
        xx = x0 + i * (sw + 14)
        a.append(f'<rect x="{xx}" y="{y0}" width="{sw}" height="{sw}" fill="#b9bdc3" stroke="{ENG}" stroke-width="1.2"/>')
        pitch = float(step) * 10; k = 0
        while k * pitch < sw - .5:
            a.append(P(f"M{xx + k*pitch + pitch/2:.2f},{y0+1} v{sw-2}", max(.35, pitch * .42), "#7b828a", extra='opacity=".85"')); k += 1
        a.append(T(xx + sw / 2, y0 + sw + 12, "S " + step, 0.75, ENG, "middle", 0.1))
    for i, ln in enumerate(["DESIGNED, PROGRAMMED", "AND MACHINED BY THE", "PERSON WHO HANDED", "IT TO YOU."]):
        a.append(T(244, 424 + i * 16, ln, 0.88, ENG, "start", 0.2))
    a.append(vernier(jb, 404, -1))
    a.append(T(jb - 32, 409, "0", 0.75, ENG, "end")); a.append(T(jb - 32, 509, "10", 0.75, ENG, "end"))
    a.append(T(244, 502, "VERNIER 0.1 AT THE JOINT", 0.72, ENG2, "start", 0.15))
    a.append(ruler(0, jb - 4, ENG))
    return card(alu_image(None, seed=7), alu, pcb, "\n".join(b), "\n".join(a))
