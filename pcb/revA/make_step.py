"""3D model of the board (STEP) for the assembly with the aluminium half.

Card frame of the CAD models, same as cad/build_card.py: X along the long edge, Y up as seen from the RECTO,
origin at the card's bottom-left corner, Z = 0 the verso face, Z = 1.70 the recto face.
The board's top face is at ripple-crest height, 0.02 below the faced recto: Z = 0.48 ... 1.68 for a 1.20 board.
Its parts hang from the back face.

The outline is rebuilt from true lines and arcs (the board file carries it as a fine polygon) and checked
against the polygon's area. Vias and copper are left out: this model is for fit, not for plots.
Runs with plain Python + CadQuery; it does not need KiCad."""
import pathlib, sys, types, math
import cadquery as cq
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_board as G
try:
    import place_parts as P
except ImportError:                      # no KiCad on this machine: read the part table without pcbnew
    sys.modules["pcbnew"] = types.SimpleNamespace(FromMM=lambda v: v, VECTOR2I=lambda *a: a)
    import place_parts as P

Z_TOP = G.CARD_T - G.SKIM                # the board's top face is at ripple-crest height
Z0 = Z_TOP - G.BOARD_T                   # back face of the board = seating plane on the aluminium
Y = lambda y: G.CARD_H - y               # board file (y down) -> CAD frame (y up)
BLACK, GOLD, CHIP, CAP, RES, LED = (0.05, 0.05, 0.06), (0.83, 0.68, 0.33), (0.12, 0.12, 0.13), (0.62, 0.52, 0.40), (0.10, 0.10, 0.10), (0.85, 0.80, 0.70)

# body sizes [mm]: length, width, height. 0402 heights are nominal catalogue values.
BODY = {"U": (1.6, 1.6, 0.50, CHIP), "C": (1.0, 0.5, 0.50, CAP), "R": (1.0, 0.5, 0.35, RES), "D": (1.0, 0.5, 0.40, LED)}

def region(extra_arc=0.0, extra_rim=0.0, offset=0.0, x_max=None):
    """The board-shaped region with true lines and arcs, as a planar face at Z = 0 in the CAD frame:
    rectangle between the rims minus the joint circle, R1.0 on the two corners that sit in the pocket.
    extra_arc / extra_rim move the joint and the rims inwards (the ledge's inner edge); offset < 0 pulls the whole
    profile in (board = pocket - GAP). x_max trims the free side; None leaves it open past the card's edge,
    which is what a cutting tool needs."""
    cx, cy = G.SPR[0], Y(G.SPR[1])
    y_lo, y_hi = G.RIM + extra_rim, G.CARD_H - G.RIM - extra_rim
    far = G.CARD_W + 10
    blank = cq.Workplane("XY").moveTo(cx, y_lo).lineTo(far, y_lo).lineTo(far, y_hi).lineTo(cx, y_hi).close().extrude(1)
    blank = blank.cut(cq.Workplane("XY").center(cx, cy).circle(G.R_JOINT + extra_arc).extrude(1))
    sel = cq.selectors.BoxSelector((cx, y_lo - 0.01, -1), (G.CARD_W - 1, y_hi + 0.01, 2))
    blank = blank.edges("|Z").edges(sel).fillet(1.0)
    wire = blank.faces("<Z").wires().val()
    if offset: wire = wire.offset2D(offset)[0]
    face = cq.Face.makeFromWires(wire)
    if x_max is not None:
        face = face.intersect(cq.Workplane("XY").rect(x_max, G.CARD_H, centered=False).extrude(1).faces("<Z").val())
        face = face.Faces()[0]
    return face

def prism(face, z0, z1):
    return cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0)).translate(cq.Vector(0, 0, z0))

def outline():
    return region(offset=-G.GAP, x_max=G.EDGE_X)

def build():
    face = outline()
    area = face.Area()
    assert abs(area - G.BOARD.area) < 0.5, (area, G.BOARD.area)
    board = cq.Workplane(obj=prism(face, Z0, Z_TOP))
    for p in G.PINS:                                     # locating holes
        board = board.cut(cq.Workplane("XY").center(p[0], Y(p[1])).circle(G.PIN_DRILL / 2).extrude(G.CARD_T + 1).translate((0, 0, -0.5)))
    for cy in G.CAST_Y:                                  # castellated half-holes on the free edge
        board = board.cut(cq.Workplane("XY").center(G.EDGE_X, Y(cy)).circle(0.4).extrude(G.CARD_T + 1).translate((0, 0, -0.5)))
    asm = cq.Assembly(name="hybrid_card_revA_board")
    asm.add(board, name="board_FR4_1.2", color=cq.Color(*BLACK))
    for p in G.PINS:                                     # gold lands around the pin holes, both faces (0.02 proud, visual only)
        ring = cq.Workplane("XY").center(p[0], Y(p[1])).circle(G.PIN_PAD / 2).circle(G.PIN_DRILL / 2).extrude(0.02)
        asm.add(ring.translate((0, 0, Z_TOP)), name=f"land_front_{G.PINS.index(p) + 1}", color=cq.Color(*GOLD))
    for ref, (lib, fp, val, pos, lcsc, fit) in P.PARTS.items():
        if not fit: continue
        l, w, h, col = BODY[ref[0]]
        if ref == "C2": l, w = w, l                      # placed at 90 deg
        body = cq.Workplane("XY").box(l, w, h, centered=(True, True, False)).translate((pos[0], Y(pos[1]), Z0 - h))
        asm.add(body, name=f"{ref}_{val.split()[0]}", color=cq.Color(*col))
    return asm, board, area

if __name__ == "__main__":
    asm, board, area = build()
    out = HERE / "out" / "hybrid_card_revA_board.step"
    asm.save(str(out))
    bb = board.val().BoundingBox()
    print(f"written {out.name}: outline area {area:.2f} mm2 (board file polygon {G.BOARD.area:.2f}), "
          f"bbox x {bb.xmin:.2f}..{bb.xmax:.2f}  y {bb.ymin:.2f}..{bb.ymax:.2f}  z {bb.zmin:.2f}..{bb.zmax:.2f}, volume {board.val().Volume():.1f} mm3")
