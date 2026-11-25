"""Assembly files in JLCPCB's column layout: BOM (one line per value) and placement list (back side only)."""
import csv, pathlib, subprocess, collections
import pcbnew
import place_parts
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
b = pcbnew.LoadBoard(str(OUT / "hybrid_card_revA.kicad_pcb"))
LCSC = {ref: v[4] for ref, v in place_parts.PARTS.items() if v[4]}
SKIP = ("ART", "ANT", "JP")
groups = collections.OrderedDict()
for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
    ref = f.GetReference()
    if ref.startswith(SKIP): continue
    key = (f.GetValue(), f.GetFPID().GetLibItemName().wx_str() if hasattr(f.GetFPID().GetLibItemName(), "wx_str") else str(f.GetFPID().GetLibItemName()))
    groups.setdefault(key, []).append(ref)
with open(OUT / "hybrid_card_revA_BOM_JLC.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (val, fp), refs in groups.items():
        w.writerow([val, ",".join(refs), fp, LCSC.get(refs[0], "")])
pos = OUT / "_pos.csv"
subprocess.run(["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "back", "-o", str(pos), str(OUT / "hybrid_card_revA.kicad_pcb")], check=True, capture_output=True)
rows = list(csv.DictReader(open(pos)))
with open(OUT / "hybrid_card_revA_CPL_JLC.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        if r["Ref"].startswith(SKIP): continue
        w.writerow([r["Ref"], r["PosX"], r["PosY"], "Bottom", r["Rot"]])
pos.unlink()
print(open(OUT / "hybrid_card_revA_BOM_JLC.csv").read()); print(open(OUT / "hybrid_card_revA_CPL_JLC.csv").read())
