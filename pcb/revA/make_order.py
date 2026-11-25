"""Order package for JLCPCB: Gerbers + drill files zipped, with the BOM and placement files beside them.
Layers sent: the four copper layers, both masks, both pastes, both silkscreens, the outline. The User layers
(card outline, notes) stay at home: a fab could read a second outline there."""
import pathlib, subprocess, zipfile, shutil, re, collections
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"; PCB = OUT / "hybrid_card_revA.kicad_pcb"
G = OUT / "gerbers"; ORDER = OUT / "order"
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
for d in (G, ORDER):
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
run = lambda *a: subprocess.run(a, check=True, capture_output=True, text=True)
run("kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask", "--exclude-refdes", "--exclude-value", "-o", str(G) + "/", str(PCB))
run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
    "--drill-origin", "absolute", "--excellon-oval-format", "route", "--excellon-separate-th", "-o", str(G) + "/", str(PCB))
for f in sorted(G.iterdir()):
    if f.suffix == ".drl" and not re.search(r"^T\d+C", f.read_text(), re.M): f.unlink()          # no non-plated holes on this board
    elif f.suffix == ".gbrjob": f.unlink()
z = ORDER / "hybrid_card_revA_gerbers.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(G.iterdir()): zf.write(f, f.name)
for n in ("hybrid_card_revA_BOM_JLC.csv", "hybrid_card_revA_CPL_JLC.csv"): shutil.copy(OUT / n, ORDER / n)
print("gerbers:", ", ".join(f"{f.name} ({f.stat().st_size // 1024} kB)" for f in sorted(G.iterdir())))
for f in G.glob("*.drl"):
    t = f.read_text(); tools = dict(re.findall(r"^(T\d+)C([\d.]+)", t, re.M)); hits = collections.Counter(); cur = None
    for line in t.splitlines():
        m = re.match(r"^(T\d+)$", line)
        if m: cur = m.group(1)
        elif cur and re.match(r"^[XY]", line): hits[cur] += 1
    print(f.name, {f"{tools[k]} mm": v for k, v in hits.items()})
print("zip:", z.name, z.stat().st_size // 1024, "kB")
