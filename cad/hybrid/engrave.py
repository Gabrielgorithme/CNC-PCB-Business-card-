"""What is engraved on the aluminium, taken from the B2 mock-up itself (design/hybrid/concept_b2.py), as regions in the
CAD frame (mm, Y up as seen from the recto, verso mirrored so it reads right when the card is turned over).

The mock-up draws every engraved line and letter as a stroked path in one of a few greys; this reads those back
and turns each stroke into the area a cutter of that width removes."""
import io, sys, pathlib
import svgelements as se
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union, substring
from shapely import affinity

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "design" / "hybrid")); sys.path.insert(0, str(ROOT / "pcb" / "revA"))
import concept_b2 as M
import gen_board as G

L, W = G.CARD_W, G.CARD_H
LINE = {M.ENG, M.ENG2, "#5d646c"}                 # engraved lines and lettering
FILL = {M.ENG, "#24282d", "#b9bdc3"}              # filled areas: arrowheads and datum triangles, QR modules, scallop patches

def _bodies():
    """The aluminium layer of each face, as the mock-up draws it, without rendering the pictures around it."""
    keep = {}
    card, alu_image = M.card, M.alu_image
    M.card = lambda alu_img, alu, pcb, pcb_body, alu_body, **kw: alu_body
    M.alu_image = lambda *a, **k: ""
    try: keep["recto"], keep["verso"] = M.recto(), M.verso()
    finally: M.card, M.alu_image = card, alu_image
    return keep

def _polylines(el):
    p = abs(se.Path(el) if not isinstance(el, se.Path) else el)
    res = []
    for sub in p.as_subpaths():
        sp = se.Path(sub)
        if len(sp) < 2: continue
        if any(isinstance(g, (se.Arc, se.CubicBezier, se.QuadraticBezier)) for g in sp):
            n = max(8, int(sp.length(error=1e-3) / 1.5) * 4)
            pts = [(q.x, q.y) for q in (sp.point(i / n) for i in range(n + 1))]
        else:
            pts = [(g.end.x, g.end.y) for g in sp if isinstance(g, (se.Move, se.Line, se.Close)) and g.end is not None]
        pts = [q for i, q in enumerate(pts) if i == 0 or q != pts[i - 1]]
        if len(pts) >= 2: res.append(pts)
    return res

def _dashed(line, pattern):
    out, pos, i = [], 0.0, 0
    while pos < line.length:
        seg = pattern[i % len(pattern)]
        if i % 2 == 0: out.append(substring(line, pos, min(pos + seg, line.length)))
        pos += seg; i += 1
    return out

def region(svg_body, mirror):
    doc = se.SVG.parse(io.StringIO(f'<svg xmlns="http://www.w3.org/2000/svg">{svg_body}</svg>'), reify=False)
    shapes = []
    for el in doc.elements():
        if not isinstance(el, se.Shape) or not hasattr(el, "values"): continue
        v = el.values
        stroke, fill = v.get("stroke") in LINE, v.get("fill") in FILL
        if not (stroke or fill): continue
        w = float(v.get("stroke-width", 1))
        dash = [float(t) for t in v["stroke-dasharray"].replace(",", " ").split()] if v.get("stroke-dasharray") else None
        for pts in _polylines(el):
            if fill and len(pts) >= 3: shapes.append(Polygon(pts).buffer(0))
            if stroke:
                line = LineString(pts)
                for part in (_dashed(line, dash) if dash else [line]):
                    if part.length > 1e-6: shapes.append(part.buffer(w / 2, cap_style=3, join_style=2, mitre_limit=1.5))   # square ends: a third of the vertices of round ones
    u = unary_union([s for s in shapes if not s.is_empty])
    u = affinity.affine_transform(u, [0.1, 0, 0, -0.1, 0, W])                 # mock-up units (0.1 mm, y down) -> mm, y up
    return affinity.affine_transform(u, [-1, 0, 0, 1, L, 0]) if mirror else u

def faces():
    """(recto, verso) engraving regions, already limited to where there is aluminium to engrave."""
    y = lambda g: affinity.affine_transform(g, [1, 0, 0, -1, 0, W])
    card = box(0, 0, L, W).buffer(-G.CARD_R).buffer(G.CARD_R, 32)
    far = lambda arc, rim: box(G.SPR[0], G.RIM + rim, L + 10, W - G.RIM - rim).difference(Point(G.SPR).buffer(G.R_JOINT + arc, 256)).buffer(-1, 64).buffer(1, 64)
    pocket, window = y(far(0, 0)), y(far(G.LEDGE, G.RIM_LEDGE))
    spr = (G.SPR[0], W - G.SPR[1])
    flex = Point(spr).buffer(13.0 + 0.3, 64).difference(Point(spr).buffer(4.8 - 0.3, 64))
    hole = Point(5.0, W - 5.0).buffer(1.5 + 0.25, 32)
    b = _bodies()
    recto = region(b["recto"], False).intersection(card.buffer(-0.3)).difference(pocket.buffer(0.3)).difference(flex).difference(hole)
    verso = region(b["verso"], True).intersection(card).difference(window.buffer(0.3)).difference(flex).difference(hole)
    return recto, verso

if __name__ == "__main__":
    r, v = faces()
    n = lambda g: len(g.geoms) if hasattr(g, "geoms") else 1
    print("recto %.1f mm2 in %d pieces, verso %.1f mm2 in %d pieces" % (r.area, n(r), v.area, n(v)))
