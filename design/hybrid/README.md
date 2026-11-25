# Hybrid card (v2): aluminium + PCB mockups

Mockup generator for the second card: a milled 7075 half and a four-layer PCB half, joined along a ripple wavefront.

- `concept_b2.py` is the chosen direction (B2, "Wavefront"): aluminium on three sides of the board, joint on the
  18th ripple crest (R36), 1.2 mm board on a 0.5 mm ledge, two locating pins milled from the solid.
- `concept_a.py`, `concept_b.py`, `concept_c.py` are the three first explorations, kept for reference.
- `lib.py` holds the shared drawing code. Geometry is built with shapely, 10 units = 1 mm, same convention as `design/v3`.

Run `python3 design/hybrid/generate.py b2` (needs numpy, pillow, shapely, segno and `rsvg-convert`). It writes
SVG + PNG for recto, verso and the lit-from-behind view into `design/hybrid/out/`. Only the three B2 previews are
committed; the generated SVG/PNG are ignored.

These are pictures, not fabrication data: antenna turn counts are indicative, the lit view is a rendering of the
intended effect, and the BGA, bus and meanders on the PCB are decorative.
