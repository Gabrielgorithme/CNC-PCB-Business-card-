"""Draws interface.png: where the board touches the aluminium, in plan and in section, from the shared numbers."""
import sys, math, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Rectangle, Circle
from shapely.geometry import Point, box
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "pcb" / "revA"))
import gen_board as G

T = G.CARD_T; ZT = T - G.SKIM; ZS = ZT - G.BOARD_T; ZG = ZS - G.GLUE_GAP; ZP = ZT - G.PIN_TOP_BELOW
INK, MUTED = "#16181c", "#5b626b"
ALU, ALU_E, SEAT, GLUE, FR4, GOLD, WIN = "#d3d7dc", "#8c939b", "#2f6fde", "#f0a63a", "#17181b", "#c9a44a", "#ffffff"

def shp(ax, g, **kw):
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.is_empty: continue
        ax.add_patch(MPoly(np.array(p.exterior.coords), closed=True, **kw))

def note(ax, text, xy, xytext, ha="left", va="center"):
    ax.annotate(text, xy=xy, xytext=xytext, ha=ha, va=va, fontsize=12.5, color=INK, linespacing=1.25,
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.9, shrinkA=2, shrinkB=0))
    ax.plot(*xy, "o", ms=3.2, color=INK)

fig = plt.figure(figsize=(9, 12.6), dpi=150)
fig.patch.set_facecolor("white")

# ------------------------------------------------------------------ plan, seen from the recto, pocket empty
ax = fig.add_axes([0.03, 0.50, 0.94, 0.44]); ax.set_aspect("equal"); ax.axis("off")
card = box(0, 0, G.CARD_W, G.CARD_H).buffer(-G.CARD_R).buffer(G.CARD_R, 32)
far = box(G.SPR[0], G.RIM, G.CARD_W + 10, G.CARD_H - G.RIM).difference(Point(G.SPR).buffer(G.R_JOINT, 256))
pocket = far.buffer(-1, 64).buffer(1, 64)
window = box(G.SPR[0], G.RIM + G.RIM_LEDGE, G.CARD_W + 10, G.CARD_H - G.RIM - G.RIM_LEDGE).difference(Point(G.SPR).buffer(G.R_JOINT + G.LEDGE, 256)).buffer(-1, 64).buffer(1, 64)
inner = pocket.buffer(-G.SEAT_W, 64)
shp(ax, card, fc=ALU, ec=ALU_E, lw=1.2)
shp(ax, pocket.intersection(card), fc=SEAT, ec="none")
shp(ax, inner.intersection(card), fc=GLUE, ec="none")
shp(ax, window.intersection(card), fc=WIN, ec=ALU_E, lw=0.8)
ax.plot([G.CARD_W, G.CARD_W], [G.RIM + G.RIM_LEDGE, G.CARD_H - G.RIM - G.RIM_LEDGE], color="white", lw=3)
ax.add_patch(Circle(G.PINS[0], G.PIN_D / 2, fc=ALU, ec=INK, lw=1.0))
shp(ax, Point(G.PINS[1]).buffer(G.PIN_D / 2, 32).intersection(box(G.PINS[1][0] - 2, G.PINS[1][1] - G.PIN_B_FLATS / 2, G.PINS[1][0] + 2, G.PINS[1][1] + G.PIN_B_FLATS / 2)), fc=ALU, ec=INK, lw=1.0)
ax.add_patch(Circle(G.PINS[1], G.PIN_DRILL / 2, fc='none', ec=INK, lw=0.5, ls=':'))
ax.add_patch(Circle(G.SPR, 13, fc="none", ec=ALU_E, lw=0.8)); ax.add_patch(Circle((5, 5), 1.5, fc="white", ec=ALU_E, lw=0.8))
ax.plot([0, G.SPR[0] + math.sqrt(G.R_JOINT ** 2 - (G.BAND_Y - G.SPR[1]) ** 2)], [G.BAND_Y, G.BAND_Y], color=ALU_E, lw=0.8)
ax.set_xlim(-1, G.CARD_W + 1); ax.set_ylim(G.CARD_H + 1, -1)
pa, pb = G.PINS
note(ax, "pin A,\nround Ø2.00", pa, (58.5, 10.5))
note(ax, "pin B, a blade\nacross A–B", pb, (58.5, 32.5))
note(ax, "dry seat (blue), 0.50 wide,\nall along the wall", (77.0, G.RIM + 0.25), (74.0, 9.0), ha="center", va="top")
note(ax, "glue land (orange),\n0.08 lower", (G.SPR[0] + G.R_JOINT + 2.3, G.SPR[1]), (60.5, 22.5))
ax.text(73.0, 42.0, "open window:\nnothing behind the\nantenna or the parts", fontsize=12.5, color=MUTED, ha="center", va="center", linespacing=1.25)
ax.plot(*zip((pa[0] - 4.5, pa[1] + 2.0), (pa[0] + 4.5, pa[1] - 2.0)), color=INK, lw=1.2, ls=(0, (6, 2, 1, 2)))
ax.text(pa[0] - 5.2, pa[1] + 2.6, "S", fontsize=13, color=INK, ha="center", va="center", weight="bold")
ax.text(pa[0] + 5.2, pa[1] - 2.6, "S", fontsize=13, color=INK, ha="center", va="center", weight="bold")
fig.text(0.04, 0.955, "Aluminium half, pocket empty, seen from the recto", fontsize=15, color=INK, weight="bold")

# ------------------------------------------------------------------ section S-S through pin A, along a radius
ax = fig.add_axes([0.03, 0.06, 0.94, 0.36]); ax.set_aspect("equal"); ax.axis("off")
R0, R1 = 34.6, 41.6
rip = lambda r: -G.SKIM - 0.12 * (0.5 - 0.5 * np.cos(2 * np.pi * r / 2.0)) * np.exp(-r / 70.0)
rr = np.linspace(R0, G.R_JOINT, 80)
alu = [(R0, 0)] + [(r, T + rip(r)) for r in rr] + [(G.R_JOINT, ZS), (G.R_JOINT + G.SEAT_W, ZS), (G.R_JOINT + G.SEAT_W, ZG)]
c = G.PIN_CHAMFER; p0, p1 = G.PIN_R - G.PIN_D / 2, G.PIN_R + G.PIN_D / 2
alu += [(p0, ZG), (p0, ZP - c), (p0 + c, ZP), (p1 - c, ZP), (p1, ZP - c), (p1, ZG), (G.R_JOINT + G.LEDGE, ZG), (G.R_JOINT + G.LEDGE, 0)]
ax.add_patch(MPoly(alu, closed=True, fc=ALU, ec=ALU_E, lw=1.2))
h0, h1 = G.PIN_R - G.PIN_DRILL / 2, G.PIN_R + G.PIN_DRILL / 2
b0 = G.R_JOINT + G.GAP
ax.add_patch(Rectangle((G.R_JOINT + G.SEAT_W, ZG), h0 - G.R_JOINT - G.SEAT_W, G.GLUE_GAP, fc=GLUE, ec="none"))
ax.add_patch(Rectangle((h1, ZG), G.R_JOINT + G.LEDGE - h1, G.GLUE_GAP, fc=GLUE, ec="none"))
ax.add_patch(Rectangle((b0, ZS), h0 - b0, G.BOARD_T, fc=FR4, ec="none"))
ax.add_patch(Rectangle((h1, ZS), R1 - h1, G.BOARD_T, fc=FR4, ec="none"))
l0, l1 = G.PIN_R - G.PIN_PAD / 2, G.PIN_R + G.PIN_PAD / 2
for (x0, x1) in ((l0, h0), (h1, l1)):
    for zz in (ZT - 0.045, ZS): ax.add_patch(Rectangle((x0, zz), x1 - x0, 0.045, fc=GOLD, ec="none"))
for x in (h0 - 0.03, h1): ax.add_patch(Rectangle((x, ZS), 0.03, G.BOARD_T, fc=GOLD, ec="none"))
for ring in (40.0,): ax.add_patch(Rectangle((ring - 0.22, ZT - 0.045), 0.44, 0.045, fc=GOLD, ec="none"))
ax.plot([R1, R1], [ZS, ZT], color="white", lw=2)
ax.plot([R0 - 0.1, R1 + 0.1], [T, T], color=MUTED, lw=0.7, ls=(0, (4, 3)))
ax.plot([R0 - 0.1, R1 + 0.1], [0, 0], color=MUTED, lw=0.7, ls=(0, (4, 3)))
ax.text(R0 - 0.05, T + 0.07, "faced recto, Z 1.70", fontsize=11.5, color=MUTED, ha="left", va="bottom")
ax.text(R1 + 0.05, -0.08, "verso, Z 0 (datum A)", fontsize=11.5, color=MUTED, ha="right", va="top")
ax.text(35.3, 0.85, "aluminium", fontsize=13, color=INK, ha="center", va="center")
ax.text(40.6, 1.08, "board", fontsize=13, color="white", ha="center", va="center")
ax.text(G.PIN_R, 1.02, "pin A", fontsize=12.5, color=INK, ha="center", va="center")
ax.set_xlim(R0 - 0.15, R1 + 0.15); ax.set_ylim(-1.35, 3.0)
note(ax, "gap 0.10", (G.R_JOINT + G.GAP / 2, 1.25), (36.05, 2.45), ha="center", va="bottom")
note(ax, "board top at crest\nheight, 0.02 below\nthe faced recto", (40.9, ZT), (40.55, 2.45), ha="center")
note(ax, "pin top 0.05 below\nthe board, 0.15 chamfer", (G.PIN_R + 0.3, ZP), (38.0, 2.55), ha="center")
note(ax, "pin Ø2.00 in\nhole Ø2.10", (h1 + 0.025, 0.95), (39.6, -0.85), ha="center")
note(ax, "dry seat 0.50:\nsets the height", (G.R_JOINT + 0.3, ZS), (35.55, -0.78), ha="center")
note(ax, "glue, 0.08 bond line\nledge 0.40 here", (37.3 - 0.45, ZG + 0.04), (37.55, -0.78), ha="center")
fig.text(0.04, 0.435, "Section S–S through pin A (to scale, 1.20 board)", fontsize=15, color=INK, weight="bold")
fig.savefig(HERE / "interface.png", facecolor="white")
print("written interface.png")
