"""Renders the hybrid card mockups: python3 design/hybrid/generate.py [a b c]
Writes SVG + PNG for recto, verso and the held-to-the-light view of each concept into design/hybrid/out/."""
import importlib, pathlib, subprocess, sys

OUT = pathlib.Path(__file__).parent / "out"

def render(name, svg, width=1832):
    f = OUT / f"{name}.svg"; f.write_text(svg, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-w", str(width), str(f), "-o", str(OUT / f"{name}.png")], check=True)

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for k in (sys.argv[1:] or ["a", "b", "c", "b2"]):
        m = importlib.import_module(f"concept_{k}")
        render(f"{k.upper()}_recto", m.recto())
        render(f"{k.upper()}_verso", m.verso())
        render(f"{k.upper()}_backlit", m.recto(backlit=True))
        print(k, "ok")
