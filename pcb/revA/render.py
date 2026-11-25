"""Realistic preview of the fabricated board from KiCad's own plots (one SVG per layer, composited):
black mask, gold where copper is exposed, a faint ridge where copper is under mask, tan where FR-4 is bare."""
import pathlib, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
PCB = OUT / "hybrid_card_revA.kicad_pcb"
W = 2600

def layer(name, mirror=False, W=W):
    svg = OUT / f"_l_{name.replace('.', '_')}.svg"
    cmd = ["kicad-cli", "pcb", "export", "svg", "--layers", name, "--black-and-white", "--page-size-mode", "2", "--exclude-drawing-sheet", "-o", str(svg), str(PCB)]
    if mirror: cmd.insert(4, "--mirror")
    subprocess.run(cmd, check=True, capture_output=True)
    png = svg.with_suffix(".png")
    subprocess.run(["rsvg-convert", "-w", str(W), "-b", "white", str(svg), "-o", str(png)], check=True)
    a = np.asarray(Image.open(png).convert("L"), dtype=np.float32) / 255.0
    svg.unlink(); png.unlink()
    return 1.0 - a          # 1 where the layer has material

def face(cu, mask, silk, mirror, lit_layers=None, W=W, pad=40):
    """pad=0 crops to the board's bounding box exactly, which is what a decal on the 3D model needs."""
    c, m, s, e = layer(cu, mirror, W), layer(mask, mirror, W), layer(silk, mirror, W), layer("Edge.Cuts", mirror, W)
    h, w = c.shape
    # board interior = flood from the edge plot
    from scipy import ndimage
    inside = ndimage.binary_fill_holes(e > 0.5)
    img = np.zeros((h, w, 3), np.float32) + np.array([0.055, 0.058, 0.066])
    rng = np.random.default_rng(1)
    base = np.array([0.045, 0.047, 0.052]) + rng.normal(0, 0.004, (h, w, 1))
    relief = np.array([0.105, 0.108, 0.118])
    gold = np.array([0.86, 0.71, 0.36]); fr4 = np.array([0.70, 0.67, 0.49]); white = np.array([0.93, 0.94, 0.93])
    col = base + (relief - base) * c[..., None] * 0.9
    exposed = m[..., None]
    col = col * (1 - exposed) + (fr4 * (1 - c[..., None]) + gold * c[..., None]) * exposed
    col = col * (1 - s[..., None] * (1 - exposed)) + white * s[..., None] * (1 - exposed)
    if lit_layers:                               # held against the light: copper on any layer blocks it
        blocked = np.clip(sum(layer(l, mirror) for l in lit_layers) + c, 0, 1)
        glow = (m * (1 - blocked))
        g = np.asarray(Image.fromarray((glow * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), dtype=np.float32) / 255
        col = col * 0.16 + np.array([1.0, 0.72, 0.30]) * glow[..., None] + np.array([1.0, 0.6, 0.2]) * g[..., None] * 0.6
    img = np.where(inside[..., None], col, img)
    ys, xs = np.where(inside)
    if pad == 0: img = np.where(inside[..., None], col, base * np.ones_like(col))      # mask colour outside too, so no seam shows at the edge
    img = img[max(0, ys.min() - pad):ys.max() + pad + 1, max(0, xs.min() - pad):xs.max() + pad + 1]
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

if __name__ == "__main__":
    face("F.Cu", "F.Mask", "F.SilkS", False).convert("RGB").save(OUT / "preview_front.jpg", quality=90)
    face("B.Cu", "B.Mask", "B.SilkS", True).convert("RGB").save(OUT / "preview_back.jpg", quality=90)
    face("F.Cu", "F.Mask", "F.SilkS", False, ["In1.Cu", "In2.Cu", "B.Cu"]).convert("RGB").save(OUT / "preview_front_lit.jpg", quality=90)
    # decals for the 3D model: exact crop to the board's bounding box, twice the resolution
    face("F.Cu", "F.Mask", "F.SilkS", False, W=2 * W, pad=0).convert("RGB").save(OUT / "decal_front.jpg", quality=92)
    face("B.Cu", "B.Mask", "B.SilkS", True, W=2 * W, pad=0).convert("RGB").save(OUT / "decal_back.jpg", quality=92)
    print("previews written")
