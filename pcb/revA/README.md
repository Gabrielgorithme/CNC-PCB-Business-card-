# Hybrid card, PCB half, rev A (first article / test coupon)

The board half of the B2 "Wavefront" card, generated from the same numbers as the mockup in `design/hybrid/`.
Rev A is a real board in the real outline, with a few coupon-only features, meant to answer what the mockup cannot.

## What is in `out/`

| File | What it is |
|---|---|
| `hybrid_card_revA.kicad_pcb` / `.kicad_pro` | The board. Written in KiCad 7's format, which KiCad 10 opens. |
| `gg_card.pretty/`, `fp-lib-table` | Project footprint library (the chip's footprint). |
| `hybrid_card_revA_board.step` | 3D model of the board with its parts, in the card's CAD frame (see below). For the assembly with the aluminium half. |
| `preview_front.jpg`, `preview_back.jpg`, `preview_front_lit.jpg` | Previews composited from KiCad's own layer plots. The back is shown as seen from the back. The lit view is a model, not a measurement. |
| `hybrid_card_revA_BOM_JLC.csv`, `..._CPL_JLC.csv` | Assembly files in JLCPCB's column layout (draft). |

## Geometry shared with the aluminium half (card frame, mm, origin = card top-left seen from the recto)

- Flexure / ripple centre (19.0, 21.5). Joint on the 18th ripple crest, R36.
- Rims 3.18 top and bottom. Ledge 4.0 along the joint, 1.5 under the rims.
- Board outline drawn 0.10 smaller than the nominal pocket per side, R1.0 on the corners that sit in the pocket.
  The pocket is meant to be machined to the delivered boards.
- Two locating pins at R38, -24 deg and +22 deg: (53.71, 6.04) and (54.23, 35.74). Plated holes 2.10, lands 3.20.

## The tag

NT3H2111 (NTAG I2C plus, 50 pF input capacitance, energy-harvesting output). VOUT feeds 220 nF, then 33 ohm and a red LED
(a standard top-emitting 0402 on the back). The resistor only matters in a strong field; 33 ohm is in JLCPCB's basic list.
Antenna: 7-turn rectangular spiral on the back, 14.1 x 29.2 mm, 0.20 track / 0.15 gap, placed against the board's free
edge, away from the aluminium. Calculated free-air inductance 2.10 uH (`coil.py`, Greenhouse method; expect about 10 % error).

It is deliberately tuned high. Three C0G capacitors sit behind solder bridges (bridge the two pads of JP1..JP3 with solder):

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

## Coupon-only features

- Back, under the ledge once assembled: copper text at 0.5 / 0.6 / 0.7 / 0.8 / 1.0 mm and lines at 0.09 / 0.10 / 0.127 / 0.15 / 0.20 mm.
- The top run of the antenna is left bare of mask, as a sample of exposed fine-pitch gold. The rest is under mask.

## 3D model

`hybrid_card_revA_board.step` uses the same frame as `cad/build_card.py`: X along the long edge, Y up as seen from the
recto, origin at the card's bottom-left corner, Z = 0 the verso face, Z = 1.70 the recto face. The board occupies
Z = 0.50 ... 1.70 and its parts hang down to Z = 0. Dropped into the card's assembly at the origin it is in place.

The outline is rebuilt from true lines and arcs. Vias and copper are not modelled. Part bodies are plain blocks
(chip 1.6 x 1.6 x 0.5 from the datasheet; 0402 heights are nominal catalogue values).

## Thickness: 1.2 mm board on a 0.50 mm ledge

Card 1.70, board 1.20, flush with the recto. The recess behind the board is therefore 0.50 deep, and the chip and the
0402 capacitors are 0.50 tall: they come flush with the aluminium back, with nothing to spare. The solder under them
adds a few hundredths, so expect them to stand that much proud of the verso plane, inside the recess.
The stack-up in the board file is a nominal split that adds up to 1.20; the fab's standard 1.2 mm 4-layer stack-up applies.

## Checks done

- Design-rule check in KiCad 10.0.8 (through kicad-mcp-pro on the PC) and in KiCad 7: same result both times,
  0 unconnected items, 0 courtyard issues, 8 violations. All 8 are the castellated half-holes sitting on the
  board edge, which is what a castellated hole is.
- Rendered from the plots and looked at, front, back and lit.
- 3D model against KiCad's own STEP export of the board: same bounding box, same thickness, outline area equal to the
  board file's polygon to 0.01 mm2. Volumes differ by 7 mm3, which is the vias.
- Unused chip pins: SCL, SDA and FD are left open and VCC is not connected. NXP's support answers on their community
  forum say these may float when unused.
- Part numbers (JLCPCB parts library, looked up 2026-11-25): U1 C710403, D1 C130719 (NationStar NCD0402R1, red),
  R1 C25105 (33 ohm), C2 C16772 (220 nF X7R 16 V), C3 C1576 (6.8 pF C0G), C4 C1547 (12 pF C0G), C5 C1555 (22 pF C0G).
  Stock was not checked.

## Before ordering

1. **Chip footprint.** The land pattern is drawn from the package dimensions (terminals 0.2 x 0.4, three per side at
   0.5 mm, one centred on each of the other two sides). Arrangement and pitch agree with NXP's reflow footprint for
   SOT902-1 and the pin figures of SOT902-2 parts. NXP's reflow drawing for SOT902-3 itself (`sot902-3_fr`) has not
   been seen, hence the name. Compare with that drawing, or with the footprint JLCPCB shows for C710403, then rename.
2. **Placement rotations** in the CPL file are KiCad's raw values. Check U1 and D1 in JLCPCB's placement preview;
   the passives are symmetric.
3. **LED direction.** A standard LED on the back shines away from the board. Whether enough light comes back into the
   slot off the phone is what this coupon tests.

## Order options this design assumes

4 layers, 1.2 mm, black mask, ENIG, castellated holes: yes.

## Rebuild

`./build.sh` (needs KiCad's Python module `pcbnew`, `kicad-cli`, shapely, numpy, scipy, pillow, `rsvg-convert`;
`make_step.py` needs CadQuery and runs without KiCad).
