# Hybrid card, PCB half, rev A

The board half of the B2 "Wavefront" card, generated from the same numbers as the mockup in `design/hybrid/`.
Rev A is ordered as the production batch (20 to 40 cards), not as a test coupon first: antenna tuning, the one thing
that cannot be settled on paper, is done by hand on the batch through the solder bridges.

## What is in `out/`

| File | What it is |
|---|---|
| `hybrid_card_revA.kicad_pcb` / `.kicad_pro` | The board. Written in KiCad 7's format, which KiCad 10 opens. |
| `gg_card.pretty/`, `fp-lib-table` | Project footprint library (the chip's footprint). |
| `hybrid_card_revA_board.step` | 3D model of the board with its parts, in the card's CAD frame (see below). For the assembly with the aluminium half. |
| `preview_front.jpg`, `preview_back.jpg`, `preview_front_lit.jpg` | Previews composited from KiCad's own layer plots. The back is shown as seen from the back. The lit view is a model, not a measurement. |
| `hybrid_card_revA_BOM_JLC.csv`, `..._CPL_JLC.csv` | Assembly files in JLCPCB's column layout (draft). |
| `decal_front.jpg`, `decal_back.jpg` | The same pictures cropped exactly to the board's bounding box (43.565 x 47.42 mm, 54 px/mm), to lay on the 3D model's faces. The back one is as seen from the back. |

## Geometry shared with the aluminium half (card frame, mm, origin = card top-left seen from the recto)

- Flexure / ripple centre (19.0, 21.5). Joint on the 18th ripple crest, R36.
- Rims 3.18 top and bottom. Ledge 4.0 along the joint, 1.5 under the rims.
- Board outline drawn 0.10 smaller than the nominal pocket per side, R1.0 on the corners that sit in the pocket.
  The pocket is meant to be machined to the delivered boards.
- Two locating pins at R38, -24 deg and +22 deg: (53.71, 6.04) and (54.23, 35.74). Plated holes 2.10, lands 2.80.
- The free edge stops 0.10 inside the card's edge (x = 85.50).
- Copper to edge: on the back, along the joint and the rims, nothing closer than 0.50 (the pin lands). On the front the
  gold rings come to 0.36 and the edge fingers to 0.30 of the free edge.
- How the board sits on the aluminium (seat, glue land, pins, heights) is in `cad/hybrid/README.md`.

## The tag

NT3H2111 (NTAG I2C plus, 50 pF input capacitance, energy-harvesting output). VOUT feeds 220 nF, then 33 ohm and a red LED
(a standard top-emitting 0402 on the back). The resistor only matters in a strong field; 33 ohm is in JLCPCB's basic list.
Antenna: 7-turn rectangular spiral on the back, 14.1 x 29.2 mm, 0.20 track / 0.15 gap, placed against the board's free
edge, away from the aluminium. Calculated free-air inductance 2.10 uH (`coil.py`, Greenhouse method; expect about 10 % error).

It is deliberately tuned high. Three C0G capacitors sit behind solder bridges JP1..JP3: two bare pads 0.25 apart under one
mask opening, no paste. A blob of solder closes one; wick opens it again.

| Bridges closed | Added | Tunes this inductance to 13.56 MHz | Resonance if L = 2.10 uH |
|---|---|---|---|
| none | 0 pF | 2.65 uH | 15.2 MHz |
| JP1 | 6.8 pF | 2.34 uH | 14.3 MHz |
| JP2 | 12 pF | 2.15 uH | 13.7 MHz |
| JP1+JP2 | 18.8 pF | 1.95 uH | 13.1 MHz |
| JP3 | 22 pF | 1.86 uH | 12.8 MHz |
| JP1+JP3 | 28.8 pF | 1.70 uH | 12.2 MHz |
| JP2+JP3 | 34 pF | 1.60 uH | 11.8 MHz |
| all | 40.8 pF | 1.48 uH | 11.4 MHz |

Aluminium next to the coil lowers its inductance, so the right combination is found with the board seated in a pocket:
try the combinations and keep the one with the longest read range and brightest LED.

## Decorative copper

The BGA land pattern, fan-out, castellations, edge fingers, meanders and test points connect to nothing.
Each trace with the pads it touches is its own small net (`ART_1` ... `ART_68`), so the design-rule check treats them as
intended connections and still checks their clearances.

## Hidden under the ledge (back)

- Copper text at 0.5 / 0.6 / 0.7 / 0.8 / 1.0 mm and lines at 0.10 / 0.127 / 0.15 / 0.20 / 0.25 mm: a record of what this
  fab resolves, for the next board. Nothing on the board is under 0.10.
- `JLCJLCJLCJLC` on silk at R38, 33 deg: where the fab may print its order number.

Nothing on the board is left to chance against the fab's limits any more: the antenna is fully under mask, and in the BGA
field the lands are gold while the dog-bone vias stay under mask, as on a real BGA, so no mask web there is under 0.4.

## Vernier (back)

Eleven gold ticks 1.35 deg apart just outside the ledge's edge, facing eleven ticks 1.50 deg apart engraved on the aluminium.
One step of coincidence is 0.1 mm at R40.

## 3D model

`hybrid_card_revA_board.step` uses the same frame as `cad/build_card.py`: X along the long edge, Y up as seen from the
recto, origin at the card's bottom-left corner, Z = 0 the verso face, Z = 1.70 the faced recto. The board's top face
is at ripple-crest height, Z = 1.68; a 1.20 board occupies Z = 0.48 ... 1.68. Dropped into the card's assembly at the
origin it is in place.

The outline is rebuilt from true lines and arcs. Vias and copper are not modelled. Part bodies are plain blocks
(chip 1.6 x 1.6 x 0.5 from the datasheet; 0402 heights are nominal catalogue values).

## Thickness: 1.2 mm board

Card 1.70, board 1.20 nominal. The pocket is cut to the measured thickness of the delivered boards, so the top face
lands at crest height whatever the fab delivers (their tolerance is 10 %). The parts on the back are 0.50 tall:
with a 1.20 board their lowest face is 0.02 below the verso plane, plus the solder under them.
The stack-up in the board file is a nominal split that adds up to 1.20; the fab's standard 1.2 mm 4-layer stack-up applies.

## Checks done

- Design-rule check in KiCad 10.0.8 (through kicad-mcp-pro on the PC) and in KiCad 7: same result both times,
  0 unconnected items, 0 courtyard issues, 8 violations. All 8 are the castellated half-holes sitting on the
  board edge, which is what a castellated hole is.
- Rendered from the plots and looked at, front, back and lit.
- 3D model against KiCad's own STEP export of the board: same bounding box, same thickness, outline area equal to the
  board file's polygon to 0.01 mm2. Volumes differ by 7 mm3, which is the vias.
- Chip footprint against figs. 31 (outline) and 32 (reflow footprint) of the NT3H2111_2211 data sheet, rev 3.6, looked at as
  drawings: terminal order, land size and position, the wider pin 1 land, the paste pull-back and the bare centre all match.
- Unused chip pins: SCL, SDA and FD are left open and VCC is not connected. NXP's support answers on their community
  forum say these may float when unused.
- Part numbers (JLCPCB parts library, looked up 2026-11-25): U1 C710403, D1 C130719 (NationStar NCD0402R1, red),
  R1 C25105 (33 ohm), C2 C16772 (220 nF X7R 16 V), C3 C1576 (6.8 pF C0G), C4 C1547 (12 pF C0G), C5 C1555 (22 pF C0G).
  Stock was not checked.

## Audit (2026-11-25)

An independent audit of the board file rebuilt the connectivity from the copper alone: all eight intended connections of
the tag circuit pass, no shorts, no opens, no closed copper loop over the coil on any layer, inductance confirmed at
2.09 to 2.10 uH by a second method. Its findings and what was done:

| Finding | Done |
|---|---|
| Placement angles were KiCad's raw bottom-side values; JLCPCB reads the bottom mirrored | `make_assembly.py` writes 180 minus KiCad's angle |
| No pin 1 mark for U1 on silk, D1's cathode dot too small to print | 0.4 dots beside U1 pin 1 and D1's cathode |
| Pin 1 land and paste of U1 not confirmed against the drawing | Redrawn from figs. 31 and 32 as seen: every land 0.40 x 0.22 at 0.60 from centre, the pin 1 land 0.32 wide with the extra 0.10 towards the corner, paste 0.025 inside each land. The 0.10 toe added earlier is gone |
| Castellations: 0.15 ring, first hole 2.32 from the corner | Pads 1.3 high (0.25 ring), row moved down 0.7 (3.02 from the corner) |
| A width clamp made every ladder line 0.15 | Ladders bypass the clamp |
| Mask webs under 0.254 at the pin lands and in the BGA field | Ring ends pulled back from the pin lands (0.3 web); dog-bone vias now under mask |
| 0.10 ring on the 49 dog-bone vias | 0.6 pads (0.15 ring) |
| "No copper within 0.6 of any edge" was not true | Statement corrected above |
| Solder bridges were 0402 lands with paste and a mask dam | Proper open solder bridges |
| "U1" label touched the layer-marker window | Moved |

## Before ordering

1. **Placement preview.** The angles are now converted for the bottom side, but JLCPCB also applies its own offset per
   library part. In their preview, U1's pin 1 must sit by the silk dot at (65.40, 42.80) and D1's cathode by the dot at
   (63.71, 37.90), card frame.
2. **Tooling holes.** Economic assembly may add tooling holes where JLCPCB chooses. Check that option, and the edge-rail
   option, at quote.
3. **LED direction.** A standard LED on the back shines away from the board. Whether enough light comes back into the
   slot off the phone is what this coupon tests.

## Order options this design assumes

| Option | Choice |
|---|---|
| Layers, thickness | 4 layers, 1.2 mm |
| Solder mask, finish | Black, ENIG |
| Castellated holes | Yes |
| Outline tolerance | The precision option (+/-0.1) if offered |
| Mark on PCB (order number) | "Specify position": the `JLCJLCJLCJLC` text is under the ledge. Or pay to remove the mark |
| Confirm production file / parts placement | Yes to both: this is where a rotated U1 or D1 gets caught |
| Assembly | Bottom side only; JP1..JP3 are not parts |
| Panel, rails, tooling holes | The curved edge and the castellated edge must stay clean. If the fab needs tabs or mouse-bites, ask for them on the two straight edges only (y = 3.28 and y = 50.70) |

## Rebuild

`./build.sh` (needs KiCad's Python module `pcbnew`, `kicad-cli`, shapely, numpy, scipy, pillow, `rsvg-convert`;
`make_step.py` needs CadQuery and runs without KiCad).
