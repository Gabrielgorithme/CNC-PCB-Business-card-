"""Aluminium half of the hybrid card, rev A: machining geometry (no engraving), and the assembly with the board.

Frame, as cad/build_card.py: X along the long edge, Y up as seen from the RECTO, origin at the card's bottom-left
corner, Z = 0 the verso face (datum A), Z = 1.70 the faced recto.

Every number of the interface comes from pcb/revA/gen_board.py, which also draws the board, so the two halves
cannot drift apart. The interface itself is described in README.md next to this file.

    python3 build_alu.py                 nominal 1.20 board
    python3 build_alu.py --board-t 1.17  pocket depth for boards that measure 1.17
"""
import sys, math, pathlib, argparse
import numpy as np
import cadquery as cq
from shapely.geometry import LineString
from shapely.ops import unary_union

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "pcb" / "revA"))
import gen_board as G
import make_step as B

L, W, T = G.CARD_W, G.CARD_H, G.CARD_T
Y = B.Y
CHAMFER = 0.15                                   # outer edges, both faces
R_POCKET, R_BOSS, WEB, SLOT_W = 13.0, 4.8, 0.40, 2.0   # flexure, as on v1; slots 2.0 since 2026-11-26 (2 mm end mill on the same centrelines)
FLEX_DEPTH = (T - WEB) / 2
HOLE = (5.0, W - 5.0, 3.0)                       # x, y, diameter
LAMBDA, AMP, DECAY = 2.0, 0.12, 70.0             # ripple: wavelength, amplitude at the source, decay length
SPR = (G.SPR[0], Y(G.SPR[1]))
BAND_Y = Y(G.BAND_Y)                             # below this line the recto stays flat (name band, bottom rim)
PINS = [(p[0], Y(p[1])) for p in G.PINS]         # A (round, upper), B (relieved, lower)
ALU, DENSITY = (0.78, 0.80, 0.82), 2.81e-3


def levels(board_t):
    z_top = T - G.SKIM                           # board top = ripple crest height
    z_seat = z_top - board_t                     # dry seating land
    return dict(top=z_top, seat=z_seat, glue=z_seat - G.GLUE_GAP, pin=z_top - G.PIN_TOP_BELOW)


def pin_solids(z):
    """Pin A is round. Pin B keeps its full diameter across the line A-B and is relieved along it, so the pair
    locates the board without fighting the hole-to-hole distance."""
    h = z["pin"] - z["glue"]
    a = cq.Workplane("XY").circle(G.PIN_D / 2).extrude(h).faces(">Z").chamfer(G.PIN_CHAMFER).val()
    ang = math.degrees(math.atan2(PINS[1][1] - PINS[0][1], PINS[1][0] - PINS[0][0]))
    slab = cq.Workplane("XY").box(G.PIN_B_FLATS, 4, h, centered=(True, True, False)).val().rotate((0, 0, 0), (0, 0, 1), ang)
    b = cq.Workplane("XY").circle(G.PIN_D / 2).extrude(h).val().intersect(slab)
    b = cq.Workplane(obj=b).faces(">Z").chamfer(G.PIN_CHAMFER).val()
    return [s.translate(cq.Vector(p[0], p[1], z["glue"])) for s, p in zip((a, b), PINS)]


def build(board_t=G.BOARD_T, ripple=True):
    z = levels(board_t)
    card = (cq.Workplane("XY").box(L, W, T, centered=False).edges("|Z").fillet(G.CARD_R)
            .faces("+Z or -Z").edges().chamfer(CHAMFER)).val()

    # ripple: a revolve about the flexure centre, everywhere on the recto above the name band
    if ripple:
        r = np.arange(14.2, 72.0, 0.1)
        h = -G.SKIM - AMP * (0.5 - 0.5 * np.cos(2 * np.pi * r / LAMBDA)) * np.clip((r - 14.2) / 1.5, 0, 1) * np.exp(-r / DECAY)
        pts = [(float(a), float(T + b)) for a, b in zip(r, h)]
        prof = (cq.Workplane("XZ").moveTo(*pts[0]).spline(pts[1:], includeCurrent=True)
                .lineTo(pts[-1][0], T + 1).lineTo(pts[0][0], T + 1).close())
        tool = prof.revolve(360, (0, 0, 0), (0, 1, 0)).val().translate(cq.Vector(SPR[0], SPR[1], 0))
        region = cq.Workplane("XY").box(L, W - BAND_Y, 4, centered=False).translate((0, BAND_Y, 0)).val()
        card = card.cut(tool.intersect(region))

    # flexure, as on v1: pocket from both faces, boss at full thickness, three spiral slots through the web
    ring = cq.Workplane("XY").center(*SPR).circle(R_POCKET).circle(R_BOSS).extrude(FLEX_DEPTH).val()
    card = card.cut(ring).cut(ring.translate(cq.Vector(0, 0, T - FLEX_DEPTH)))
    for k in range(3):
        sp = []
        for i in range(81):
            a = math.radians(k * 120 - 90 + 205 * i / 80); rr = 6.2 + (11.8 - 6.2) * i / 80
            sp.append((SPR[0] + rr * math.cos(a), SPR[1] - rr * math.sin(a)))
        g = LineString(sp).buffer(SLOT_W / 2, resolution=12)
        w = cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in list(g.exterior.coords)[:-1]], close=True)
        card = card.cut(B.prism(cq.Face.makeFromWires(w), FLEX_DEPTH - 0.1, T - FLEX_DEPTH + 0.1))
    card = card.cut(cq.Workplane("XY").center(HOLE[0], HOLE[1]).circle(HOLE[2] / 2).extrude(T).val())

    # ---- the pocket for the board, three levels
    card = card.cut(B.prism(B.region(), z["seat"], T + 1))                               # walls, down to the seating land
    card = card.cut(B.prism(B.region(offset=-G.SEAT_W), z["glue"], T + 1))               # glue land, lower by the bond line
    card = card.cut(B.prism(B.region(G.LEDGE, G.RIM_LEDGE), -1, T + 1))                  # window: nothing behind the antenna
    pins = pin_solids(z)
    for p in pins: card = card.fuse(p)
    return card.clean(), pins, z


ENGRAVE_RECTO, ENGRAVE_VERSO = 0.15, 0.10      # as on v1


def to_solids(region, z0, z1):
    solids = []
    for p in (region.geoms if hasattr(region, "geoms") else [region]):
        p = p.simplify(0.01)
        for q in ([p] if p.geom_type == "Polygon" else getattr(p, "geoms", [])):
            if q.is_empty or q.area < 1e-4: continue
            mk = lambda ring: cq.Wire.makePolygon([cq.Vector(x, y, z0) for x, y in list(ring.coords)[:-1]], close=True)
            try:
                face = cq.Face.makeFromWires(mk(q.exterior), [mk(r) for r in q.interiors])
                solids.append(cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0)))
            except Exception as e:
                print("  skipped a sliver:", e)
    return solids


def engraved(card, chunk=120):
    """The same body with the mock-up's engraving cut into both faces: a visual model, not machining geometry
    (the real engraving is V-cut along the centre lines)."""
    import engrave
    recto, verso = engrave.faces()
    print("engraving: recto %.1f mm2, verso %.1f mm2" % (recto.area, verso.area))
    solids = to_solids(recto, T - ENGRAVE_RECTO, T + 0.5) + to_solids(verso, -0.5, ENGRAVE_VERSO)
    for i in range(0, len(solids), chunk):
        card = card.cut(cq.Compound.makeCompound(solids[i:i + chunk]))
    return card


def checks(alu, pins, z, board_t):
    """Fit of the two solids. Distances in mm; everything is measured on the models, nothing is assumed."""
    B.Z0 = z["seat"]; B.Z_TOP = z["top"]
    asm, board_wp, _ = B.build()
    board = board_wp.val()
    out = {}
    out["interference mm3"] = alu.intersect(board).Volume()
    slab = lambda z0, z1: cq.Workplane("XY").box(L + 4, W + 4, z1 - z0, centered=False).translate((-2, -2, z0)).val()
    walls = alu.intersect(slab(z["seat"] + 0.01, T + 1))
    for p in pins: walls = walls.cut(cq.Workplane("XY").center(p.Center().x, p.Center().y).circle(G.PIN_D / 2 + 0.02).extrude(T + 2).translate((0, 0, -1)).val())
    out["board to pocket wall, min"] = board.distance(walls)
    out["board to pin A"] = board.distance(pins[0])
    out["board to pin B"] = board.distance(pins[1])
    floor = alu.intersect(slab(-1, z["glue"] + 1e-4))                 # everything at or below the glue land
    out["board to glue land"] = board.distance(floor)
    seat = alu.intersect(slab(z["seat"] - 0.005, z["seat"] + 0.005)).intersect(board.translate(cq.Vector(0, 0, -0.005)))
    out["dry seat contact area mm2"] = seat.Volume() / 0.005
    parts = [c for c in asm.children if c.name[0] in "UCRD" and c.name[1].isdigit()]
    out["parts to aluminium, min"] = min(c.obj.val().distance(alu) for c in parts)
    out["lowest part face, Z"] = min(c.obj.val().BoundingBox().zmin for c in parts)
    out["board top below faced recto"] = T - board.BoundingBox().zmax
    out["free edge inside card edge"] = L - board.BoundingBox().xmax
    out["ledge thickness under the seat"] = z["seat"]
    out["ledge thickness under the glue"] = z["glue"]
    return asm, out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--board-t", type=float, default=G.BOARD_T)
    ap.add_argument("--engrave", action="store_true", help="also write the engraved (visual) body and use it in the assembly")
    a = ap.parse_args()
    G.BOARD_T = a.board_t
    alu, pins, z = build(a.board_t)
    print("levels:", {k: round(v, 3) for k, v in z.items()})
    bb = alu.BoundingBox()
    print("valid:", alu.isValid(), " solids:", len(alu.Solids()), " bbox %.2f x %.2f x %.2f" % (bb.xlen, bb.ylen, bb.zlen),
          " faces:", len(alu.Faces()))
    asm_board, res = checks(alu, pins, z, a.board_t)
    for k, v in res.items(): print(f"  {k:36s} {v:8.3f}")
    tag = "" if abs(a.board_t - 1.20) < 1e-9 else f"_t{a.board_t:.2f}"
    cq.exporters.export(cq.Workplane(obj=alu), str(HERE / f"hybrid_card_revA_alu{tag}.step"), opt={"write_pcurves": False})
    shown = alu
    if a.engrave:
        shown = engraved(alu)
        floor = lambda zz: sum(f.Area() for f in shown.Faces() if f.geomType() == "PLANE" and abs(f.Center().z - zz) < 1e-6 and abs(abs(f.normalAt().z) - 1) < 1e-6)
        print("engraved: valid", shown.isValid(), " solids", len(shown.Solids()), " faces", len(shown.Faces()),
              " engraved floor area: recto %.1f mm2, verso %.1f mm2" % (floor(T - ENGRAVE_RECTO), floor(ENGRAVE_VERSO)))
        cq.exporters.export(cq.Workplane(obj=shown), str(HERE / f"hybrid_card_revA_alu_engraved{tag}.step"), opt={"write_pcurves": False})
    asm = cq.Assembly(name="hybrid_card_revA")
    asm.add(cq.Workplane(obj=shown), name="aluminium_7075", color=cq.Color(*ALU))
    asm.add(asm_board, name="board")
    asm.export(str(HERE / f"hybrid_card_revA_assembly{tag}.step"), write_pcurves=False)
    # fit gauge: the pocket alone, to cut in scrap and try the delivered boards in before the real part
    plain, _, _ = build(a.board_t, ripple=False)
    gauge = plain.intersect(cq.Workplane("XY").box(L - 37.0, W, T, centered=False).translate((37.0, 0, 0)).val())
    cq.exporters.export(cq.Workplane(obj=gauge), str(HERE / f"hybrid_card_revA_fit_gauge{tag}.step"), opt={"write_pcurves": False})
    print("written", f"hybrid_card_revA_alu{tag}.step", f"hybrid_card_revA_assembly{tag}.step", f"hybrid_card_revA_fit_gauge{tag}.step")
