"""ISOCP single-line lettering, from the strokes engraved on the first card.

Copied from the first card's repository (CNC-Business-card-: site/isocp.py and docs/assets/data/isocp-card.json),
so both cards carry the same letters. isocp-card.json holds 61 glyphs read out of that card's engraving artwork:
each glyph is a list of centreline polylines in font units (cap height 8.775, baseline y = 0, y up), plus its width
and side bearing. Characters the first card never used (È, À, Ç, Q, ') are built here from strokes it did use."""
import json, pathlib

FONT = json.loads((pathlib.Path(__file__).resolve().parent / "isocp-card.json").read_text(encoding="utf-8"))
G, CAP = FONT["glyphs"], FONT["cap"]


def _composites():
    E, Ea = G["E"], G["É"]
    acc = [s for s in Ea["s"] if min(p[1] for p in s) > CAP * 0.98]
    xs = [p[0] for s in acc for p in s]; ys = [p[1] for s in acc for p in s]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); cx = (x0 + x1) / 2
    grave = [[[2 * cx - x, y] for x, y in s] for s in acc]
    circ = [[[cx - (x1 - x0) * 0.6, y0], [cx, y1], [cx + (x1 - x0) * 0.6, y0]]]
    def put(base, a):
        b = G[base]
        return {"w": b["w"], "sb": b["sb"], "s": b["s"] + [[[x - cx + b["w"] / 2, y] for x, y in s] for s in a]}
    G["È"] = put("E", grave); G["Ê"] = put("E", circ); G["À"] = put("A", grave)
    G["Ù"] = put("U", grave); G["Î"] = put("I", circ); G["Ô"] = put("O", circ)
    c = G["C"]; m = c["w"] / 2
    G["Ç"] = {"w": c["w"], "sb": c["sb"], "s": c["s"] + [[[m, 0], [m, -0.9], [m + 1.0, -1.4], [m + 0.2, -2.3], [m - 0.6, -2.0]]]}
    o = G["O"]
    G["Q"] = {"w": o["w"], "sb": o["sb"], "s": o["s"] + [[[o["w"] * 0.55, CAP * 0.22], [o["w"] * 1.05, -CAP * 0.08]]]}
    cm = G[","]; top = max(p[1] for s in cm["s"] for p in s)
    G["'"] = G["’"] = {"w": cm["w"], "sb": cm["sb"], "s": [[[x, y + CAP - top] for x, y in s] for s in cm["s"]]}
_composites()


def layout(text, track=0.0):
    x, out = 0.0, []
    for ch in text:
        if ch == " ":
            x += FONT["space"] + track; continue
        g = G.get(ch) or G.get(ch.upper())
        if g is None:
            raise KeyError(f"no ISOCP stroke for {ch!r} in {text!r}")
        x += g["sb"]
        out += [[(x + px, py) for px, py in s] for s in g["s"]]
        x += g["w"] + g["sb"] + track
    return out, x


def svg(text, weight=None, track=0.0, lead=1.5, cls="", align="start"):
    """Inline SVG for one or more lines (split on '|'). Sized by CSS: height = cap * (--h); width follows the viewBox.
    weight is the stroke width as a fraction of the cap height."""
    lines = text.split("|")
    laid = [layout(t, track) for t in lines]
    width = max(w for _, w in laid)
    sw = CAP * (weight or 1 / 11)
    pad = sw
    dy = lead * CAP
    height = CAP + dy * (len(lines) - 1) + 2.4
    d = []
    for i, (strokes, w) in enumerate(laid):
        off = {"start": 0, "middle": (width - w) / 2, "end": width - w}[align]
        for s in strokes:
            d.append('<path d="M' + "L".join(f"{x + off:.2f},{i * dy - y:.2f}" for x, y in s) + '"/>')
    vb_w, vb_h = width + 2 * pad, height + 2 * pad
    return (f'<svg class="isocp {cls}" preserveAspectRatio="xMinYMid meet" viewBox="{-pad:.2f} {-CAP - pad:.2f} {vb_w:.2f} {vb_h:.2f}" '
            f'style="--h:{vb_h / CAP:.4f};--ar:{vb_w / vb_h:.4f}" aria-hidden="true" focusable="false">'
            f'<g fill="none" stroke="currentColor" stroke-width="{sw:.3f}" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(d) + "</g></svg>")
