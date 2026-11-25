"""3D model of the board (STEP) for the assembly with the aluminium half.

Card frame of the CAD models, same as cad/build_card.py: X along the long edge, Y up as seen from the RECTO,
origin at the card's bottom-left corner, Z = 0 the verso face, Z = 1.70 the recto face.
The board sits flush with the recto: Z = 0.50 ... 1.70. Its parts hang from the back face, down to Z = 0.

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

Z0 = G.CARD_T - G.BOARD_T                # back face of the board
Y = lambda y: G.CARD_H - y               # board file (y down) -> CAD frame (y up)
BLACK, GOLD, CHIP, CAP, RES, LED = (0.05, 0.05, 0.06), (0.83, 0.68, 0.33), (0.12, 0.12, 0.13), (0.62, 0.52, 0.40), (0.10, 0.10, 0.10), (0.85, 0.80, 0.70)

# body sizes [mm]: length, width, height. 0402 heights are nominal catalogue values.
BODY = {"U": (1.6, 1.6, 0.50, CHIP), "C": (1.0, 0.5, 0.50, CAP), "R": (1.0, 0.5, 0.35, RES), "D": (1.0, 0.5, 0.40, LED)}

def outline():
    """Pocket-side outline with true arcs: rectangle minus the joint circle, R1.0 on the two corners in the
    pocket, pulled in by the gap, trimmed by the card's right edge."""
    cx, cy = G.SPR[0], Y(G.SPR[1])
    y_lo, y_hi = G.RIM, G.CARD_H - G.RIM
    far = G.CARD_W + 10
    blank = cq.Workplane("XY").moveTo(cx, y_lo).lineTo(far, y_lo).lineTo(far, y_hi).lineTo(cx, y_hi).close().extrude(1)
    blank = blank.cut(cq.Workplane("XY").center(cx, cy).circle(G.R_JOINT).extrude(1))
    sel = cq.selectors.BoxSelector((cx, y_lo - 0.01, -1), (G.CARD_W - 1, y_hi + 0.01, 2))
    blank = blank.edges("|Z").edges(sel).fillet(1.0)
    wire = blank.faces("<Z").wires().val()
    inner = wire.offset2D(-G.GAP)[0]
    face = cq.Face.makeFromWires(inner)
    card = cq.Workplane("XY").rect(G.CARD_W, G.CARD_H, centered=False).extrude(1).faces("<Z").val()
    return face.intersect(card)

def build():
    face = outline()
    area = face.Area()
    assert abs(area - G.BOARD.area) < 0.5, (area, G.BOARD.area)
    board = cq.Workplane(obj=cq.Solid.extrudeLinear(face.Faces()[0] if hasattr(face, "Faces") else face, cq.Vector(0, 0, G.BOARD_T))).translate((0, 0, Z0))
    for p in G.PINS:                                     # locating holes
        board = board.cut(cq.Workplane("XY").center(p[0], Y(p[1])).circle(G.PIN_DRILL / 2).extrude(G.CARD_T + 1).translate((0, 0, -0.5)))
    for cy in G.CAST_Y:                                  # castellated half-holes on the free edge
        board = board.cut(cq.Workplane("XY").center(G.CARD_W, Y(cy)).circle(0.4).extrude(G.CARD_T + 1).translate((0, 0, -0.5)))
    asm = cq.Assembly(name="hybrid_card_revA_board")
    asm.add(board, name="board_FR4_1.2", color=cq.Color(*BLACK))
    for p in G.PINS:                                     # gold lands around the pin holes, both faces (0.02 proud, visual only)
        ring = cq.Workplane("XY").center(p[0], Y(p[1])).circle(G.PIN_PAD / 2).circle(G.PIN_DRILL / 2).extrude(0.02)
        asm.add(ring.translate((0, 0, G.CARD_T)), name=f"land_front_{G.PINS.index(p) + 1}", color=cq.Color(*GOLD))
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
