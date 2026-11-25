"""Concept A - TWINS. Straight split on the card's centreline, two radiused dovetail keys.
The Ø26 flexure on the aluminium has a Ø26 twin on the PCB: the NFC antenna. One single 1.6 mm four-layer board."""
from lib import *

URL = "https://gabrielgorithme.github.io/CNC-Business-card-/"
JX = 428
SPR, COIL = (214, 220), (642, 220)
BAND = 392

def regions():
    big = box(-300, -300, JX, H + 300)
    key_alu = Polygon([(JX - 2, 105), (JX + 50, 90), (JX + 50, 170), (JX - 2, 155)])    # aluminium tail in the PCB
    key_pcb = Polygon([(JX + 2, 275), (JX - 50, 260), (JX - 50, 340), (JX + 2, 325)])   # PCB tail in the aluminium
    alu = rounded(big.union(key_alu).difference(key_pcb), 6).intersection(CARD)
    return alu, CARD.difference(alu)

def spring_shadow(cx, cy, flip=1):
    """Inner-layer copper inside the antenna: the flexure's own outline, at 40 %."""
    def g(col):
        o = []
        for k in range(3):
            o.append(P(pl(spiral_pts(cx, cy, 25, 47, 205, k * 120 - 90, flip)), 5.2, col))
        o.append(f'<circle cx="{cx}" cy="{cy}" r="15" fill="{col}"/>')
        o.append(P(f"M{cx-56},{cy} H{cx+56} M{cx},{cy-56} V{cy+56}", 1.0, col, extra='stroke-dasharray="9 3 2 3"'))
        return "".join(o)
    return g

def recto(backlit=False):
    alu, pcb = regions()
    cx, cy = SPR
    b = []
    allowed = pcb.difference(circle(*COIL, 142)).difference(box(JX - 60, BAND - 8, W, H))
    b.append(rings(cx, cy, allowed, 150, 780, offset=10, kind="relief"))
    b.append(rings(cx, cy, allowed, 150, 470, w0=4.6, w1=1.5))
    b.append(rings(cx, cy, allowed, 480, 780, kind="relief"))
    c, p0, p1 = coil(*COIL, 128, 68, flip=1)
    b.append(c); b.append(via(*p0, 2, 4.5)); b.append(via(*p1, 2, 4.5))
    win = circle(*COIL, 58)
    if not backlit: b.append(window(win, spring_shadow(*COIL)))
    b.append(P(f"M{JX},{BAND} H{W}", 1.3, GOLD))
    b.append(T(JX + 24, 468, "GHANEM", 3.35, GOLD, "start", 1.5))
    b.append(T(JX + 24, 505, "ENGINEER", 1.15, GOLD, "start", 0.9))
    b.append(T(W - 44, 505, "GG-2027-002 · REV A", 0.8, GOLD, "end", 0.25))
    a = [spring(cx, cy, 1, "GG"), hole(50, 50)]
    a.append(P(f"M0,{BAND} H{JX}", 1.2, "#5d646c"))
    a.append(T(JX - 24, 468, "GABRIEL", 3.35, ENG, "end", 1.5))
    a.append(T(JX - 24, 505, "MANUFACTURING", 1.15, ENG, "end", 0.9))
    lit = window(win, spring_shadow(*COIL), backlit=True, led=(COIL[0], COIL[1] + 50, 70)) if backlit else None
    return card(alu_image(ripple(cx / 10, cy / 10, BAND / 10)), alu, pcb, "\n".join(b), "\n".join(a), joint_gold=True, backlit=lit)

def verso():
    alu, pcb = map(mirror, regions())
    sx, sy = W - SPR[0], SPR[1]          # flexure, seen from the back
    wx, wy = W - COIL[0], COIL[1]        # window, seen from the back
    # ---------------- PCB half (left)
    b = []
    b.append(T(wx, 44, "13.56 MHZ · NFC · TAP HERE", 1.2, GOLD, "middle", 0.3))
    b.append(T(wx, 68, "NO BATTERY ON THIS CARD.", 0.85, GOLD, "middle", 0.2))
    b.append(T(wx, 84, "YOUR PHONE POWERS THE LED.", 0.85, GOLD, "middle", 0.2))
    b.append(window(circle(wx, wy, 58), spring_shadow(wx, wy, -1)))
    # the tag circuit, routed in the open: antenna ends -> chip -> LED
    u1, d1, c1 = (wx + 104, wy + 4), (wx, wy + 76), (wx + 104, wy - 40)
    b.append(P(f"M{wx+66},{wy-64} H{u1[0]-6} V{u1[1]-8} M{wx+66},{wy+50} H{u1[0]-6} V{u1[1]+8}", 2.2, GOLD))
    b.append(P(f"M{u1[0]+6},{u1[1]+8} V{d1[1]} H{d1[0]+14} M{d1[0]-14},{d1[1]} H{wx-70} V{wy+40}", 2.2, GOLD))
    b.append(via(wx + 66, wy - 64, 2, 4.5)); b.append(via(wx + 66, wy + 50, 2, 4.5)); b.append(via(wx - 70, wy + 40, 2, 4.5))
    b.append(smd(*u1, 16, 16, "U1", lx=26, ly=4)); b.append(smd(*c1, 10, 5, "C1", rot=90, lx=20, ly=4))
    b.append(smd(*d1, 10, 5, "D1", body="#e8e2c4", lx=30, ly=18))
    b.append(T(30, 332, "GABRIEL.GHANEM@GMAIL.COM", 1.2, GOLD, "start", 0.42))
    q, n = qr(URL, 40, 358, 132, "gold"); b.append(q)
    tx = 214
    for i, ln in enumerate(["AVAILABLE", "SEPT. 2027", "", "FR-4 · 4 LAYERS · ENIG", "INNER LAYERS:", "SEE AGAINST THE LIGHT", "", "LAID OUT BY HIM,", "ETCHED IN SHENZHEN."]):
        big = i < 2
        if ln: b.append(T(tx, (364 + i * 21) if big else (364 + i * 15.5), ln, 1.3 if big else 0.8, GOLD, "start", 0.5 if big else 0.2))
    b.append(ruler(0, JX - 4, GOLD, wt=1.2))
    # ---------------- aluminium half (right)
    a = [spring(sx, sy, -1), hole(W - 50, 50)]
    a.append(P(f"M{sx-148},{sy} H{sx+148} M{sx},{sy-148} V{sy+148}", 1, ENG2, extra='stroke-dasharray="16 4 3 4"'))
    a.append(T(JX + 70, 40, "3× FLEXURE LEG", 1.05, ENG, "start", 0.35)); a.append(T(JX + 70, 58, "WEB 0.40 ±0.02", 1.1, ENG))
    s, w_ = fcf(JX + 70, 66, "profile", "0.05", ("A",)); a.append(s)
    a.append(P(f"M{JX+204},{52} h16 L{sx-28},{sy-92}", 1.2)); a.append(f'<circle cx="{sx-28}" cy="{sy-92}" r="3" fill="{ENG}"/>')
    a.append(P(f"M{sx-40},{sy+124} L{sx-52},{sy+158} H{sx+56}", 1.2)); a.append(arrow(sx - 40, sy + 124, -71))
    a.append(T(sx - 44, sy + 153, "Ø26 ±0.05", 1.1))
    # joint callouts: gap along the joint, flatness across both materials, vernier
    a.append(f'<g transform="translate({JX+17},{252}) rotate(-90)">' + T(0, 0, "GAP 0.05 MAX", 0.85, ENG, "start", 0.25) + "</g>")
    fx, fy = JX + 18, 364
    s, w_ = fcf(fx, fy, "flatness", "0.05"); a.append(s)
    a.append(P(f"M{fx+w_},{fy+12} h12 l10,-12", 1.2)); a.append(f'<circle cx="{fx+w_+22}" cy="{fy}" r="3.2" fill="{ENG}"/>')
    a.append(vernier(JX, 404, 1))
    a.append(T(JX + 30, 409, "0", 0.75, ENG)); a.append(T(JX + 30, 509, "10", 0.75, ENG))
    tx = JX + 76
    a.append(T(tx, 411, "VERNIER 0.1 · THIS CARD'S OWN", 0.78, ENG2, "start", 0.2)); a.append(T(tx, 425, "ASSEMBLY ERROR, READ AT THE JOINT", 0.78, ENG2, "start", 0.2))
    for i, ln in enumerate(["DESIGNED, PROGRAMMED AND", "MACHINED BY THE PERSON", "WHO HANDED IT TO YOU."]):
        a.append(T(tx, 450 + i * 18, ln, 1.12, ENG, "start", 0.32))
    a.append(T(W - 40, 504, "AL 7075-T6 · ISO 2768-FH", 0.75, ENG2, "end", 0.2))
    a.append(ruler(JX + 4, W, ENG))
    # the flatness leader that crosses onto the PCB is drawn over both materials
    top = P(f"M{fx},{fy+12} h-10 l-22,-12", 1.2) + f'<circle cx="{fx-32}" cy="{fy}" r="3.2" fill="{ENG}" stroke="{GOLD}" stroke-width="1"/>'
    return card(alu_image(None, seed=7), alu, pcb, "\n".join(b), "\n".join(a), joint_gold=True, extra_top=top)
