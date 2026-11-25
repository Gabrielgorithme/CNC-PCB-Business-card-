# Hybrid card, PCB half, rev A (first article / test coupon)

The board half of the B2 "Wavefront" card, generated from the same numbers as the mockup in `design/hybrid/`.
Rev A is a real board in the real outline, with a few coupon-only features, meant to answer what the mockup cannot.

## What is in `out/`

| File | What it is |
|---|---|
| `hybrid_card_revA.kicad_pcb` / `.kicad_pro` | The board. Written in KiCad 7's format, which KiCad 10 opens. |
| `gg_card.pretty/`, `fp-lib-table` | Project footprint library (the chip's provisional footprint). |
| `preview_front.jpg`, `preview_back.jpg`, `preview_front_lit.jpg` | Previews composited from KiCad's own layer plots. The back is shown as seen from the back. The lit view is a model, not a measurement. |
| `hybrid_card_revA_BOM_JLC.csv`, `..._CPL_JLC.csv` | Assembly files in JLCPCB's column layout (draft). |

## Geometry shared with the aluminium half (card frame, mm, origin = card top-left seen from the recto)

- Flexure / ripple centre (19.0, 21.5). Joint on the 18th ripple crest, R36.
- Rims 3.18 top and bottom. Ledge 4.0 along the joint, 1.5 under the rims.
- Board outline drawn 0.10 smaller than the nominal pocket per side, R1.0 on the corners that sit in the pocket.
  The pocket is meant to be machined to the delivered boards.
- Two locating pins at R38, -24 deg and +22 deg: (53.71, 6.04) and (54.23, 35.74). Plated holes 2.10, lands 3.20.

## The tag

NT3H2111 (NTAG I2C plus, 50 pF input capacitance, energy-harvesting output). VOUT feeds 220 nF, then 47 ohm and a red LED.
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

## Checks done

- KiCad 7 design-rule check: 0 unconnected pads, 8 violations. All 8 are the castellated half-holes sitting on the
  board edge, which is what a castellated hole is.
- Rendered from the plots and looked at, front, back and lit.

## Not done yet. Do not order before these.

1. **Chip footprint.** `XQFN-8_1.6x1.6mm_SOT902-3_PROVISIONAL` is drawn from the body size and a 3-1-3-1 terminal
   arrangement at 0.5 mm pitch. It has not been checked against NXP's reflow drawing for SOT902-3. Replace it with a
   verified footprint (JLCPCB/LCSC part C710403), then rerun `place_parts.py`.
2. **Design-rule check in KiCad 10.0.8.** Only KiCad 7 has checked this file.
3. **Unused chip pins.** SCL, SDA, FD and VCC are left open. The datasheet gives no guidance for the no-host case.
4. **LED direction.** A standard LED on the back shines away from the board. Whether enough light comes back into the
   slot off the phone is exactly what this coupon tests. Reverse-mount LEDs that fire through the board are 1.2 mm
   tall or more and do not fit the recess.
5. **Part numbers.** Only the chip's is filled in. LED, resistor and capacitors are picked in JLCPCB's parts tool.
6. **Placement rotations** in the CPL file are KiCad's raw values. Check them in JLCPCB's placement preview.

## Order options this design assumes

4 layers, black mask, ENIG, castellated holes: yes. Thickness: see below.

**Thickness is the open decision.** The chip is 0.5 mm tall. A 1.2 mm board on a 0.5 mm ledge puts it flush with the
aluminium back, with nothing to spare. A 1.0 mm board on a 0.7 mm ledge leaves it 0.2 mm below the surface.
The board file is set to 1.0 mm; it is one number to change.

## Rebuild

`./build.sh` (needs KiCad's Python module `pcbnew`, `kicad-cli`, shapely, numpy, scipy, pillow, `rsvg-convert`).
