"""Planar rectangular spiral: geometry + inductance (Greenhouse method: self-inductance of every straight
segment plus signed mutual inductance of every parallel pair). Lengths in mm, result in microhenry."""
import math

MU0 = 4e-7 * math.pi

def spiral(x0, y0, x1, y1, turns, pitch, end_y=None):
    """Polyline of a rectangular spiral on the rectangle (x0,y0)-(x1,y1), starting at the outer bottom-left corner,
    running up the left side first. After `turns` full turns it runs up the inner left side to end_y (if given)."""
    pts = [(x0, y1)]
    l, t, r, b = x0, y0, x1, y1
    for n in range(turns):
        pts += [(l, t), (r, t), (r, b), (l + pitch, b)]
        l += pitch; t += pitch; r -= pitch; b -= pitch
    if end_y is not None:
        pts.append((l, end_y))
    return pts

def _self(l, w, t):
    l, w, t = l * 1e-3, w * 1e-3, t * 1e-3
    return MU0 * l / (2 * math.pi) * (math.log(2 * l / (w + t)) + 0.5 + (w + t) / (3 * l))

def _F(z, d):
    return z * math.asinh(z / d) - math.sqrt(z * z + d * d)

def _mutual(a1, a2, b1, b2, d):
    """Parallel filaments spanning [a1,a2] and [b1,b2] along the same axis, distance d apart (metres)."""
    return MU0 / (4 * math.pi) * (_F(a2 - b1, d) - _F(a2 - b2, d) - _F(a1 - b1, d) + _F(a1 - b2, d))

def inductance(pts, w=0.2, t=0.035):
    segs = []
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if abs(xa - xb) < 1e-9:   # vertical: axis y, position x, direction sign
            segs.append(("v", xa, ya, yb))
        else:
            segs.append(("h", ya, xa, xb))
    L = 0.0
    for i, (oi, pi_, ai, bi) in enumerate(segs):
        L += _self(abs(bi - ai), w, t)
        for j, (oj, pj, aj, bj) in enumerate(segs):
            if j <= i or oi != oj: continue
            d = abs(pi_ - pj) * 1e-3
            if d < 1e-9: continue
            si = 1 if bi > ai else -1; sj = 1 if bj > aj else -1
            m = _mutual(min(ai, bi) * 1e-3, max(ai, bi) * 1e-3, min(aj, bj) * 1e-3, max(aj, bj) * 1e-3, d)
            L += 2 * si * sj * abs(m)
    return L * 1e6

if __name__ == "__main__":
    for n in range(4, 10):
        p = spiral(70.7, 16.5, 80.2, 47.6, n, 0.35, end_y=40.2)
        L = inductance(p)
        f = 1 / (2 * math.pi * math.sqrt(L * 1e-6 * 52e-12)) / 1e6
        print(n, "turns  L = %.2f uH   f0 with 50 pF + 2 pF stray = %.2f MHz" % (L, f))
