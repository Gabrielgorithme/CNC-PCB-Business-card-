"""Stage 2 of 2: adds the NFC tag to the stage-1 board with KiCad's own Python (pcbnew): library footprints on the
back, nets, tracks, vias. Run with the Python that ships with KiCad:  python3 place_parts.py"""
import pathlib, sys
import pcbnew
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_board as G

LIB = pathlib.Path("/usr/share/kicad/footprints")
mm = pcbnew.FromMM
V = lambda p: pcbnew.VECTOR2I(mm(p[0] + G.OX), mm(p[1] + G.OY))

# reference: (library, footprint, value, position in the card frame, LCSC part or None, populate?)
PARTS = {
    "U1": (HERE / "gg_card.pretty", "XQFN-8_1.6x1.6mm_SOT902-3_PROVISIONAL", "NT3H2111W0FHK", (66.6, 41.6), "C710403", True),
    "D1": (LIB / "LED_SMD.pretty", "LED_0402_1005Metric", "LED red 0402", (64.9, 37.9), None, True),
    "R1": (LIB / "Resistor_SMD.pretty", "R_0402_1005Metric", "47R", (66.4, 39.6), None, True),
    "C2": (LIB / "Capacitor_SMD.pretty", "C_0402_1005Metric", "220n", (69.0, 40.9), None, True),
    "C3": (LIB / "Capacitor_SMD.pretty", "C_0402_1005Metric", "6.8p C0G", (63.6, 44.2), None, True),
    "C4": (LIB / "Capacitor_SMD.pretty", "C_0402_1005Metric", "12p C0G", (63.6, 45.4), None, True),
    "C5": (LIB / "Capacitor_SMD.pretty", "C_0402_1005Metric", "22p C0G", (63.6, 46.6), None, True),
    "JP1": (LIB / "Resistor_SMD.pretty", "R_0402_1005Metric", "solder bridge", (66.6, 44.2), None, False),
    "JP2": (LIB / "Resistor_SMD.pretty", "R_0402_1005Metric", "solder bridge", (66.6, 45.4), None, False),
    "JP3": (LIB / "Resistor_SMD.pretty", "R_0402_1005Metric", "solder bridge", (66.6, 46.6), None, False),
}
V_IN, V_B, V_G1, V_G2 = G.COIL_END, (69.9, 40.2), (69.0, 39.4), (63.6, 39.4)

def main(src, dst):
    b = pcbnew.LoadBoard(str(src))
    nets = {}
    for n in ("ANT_A", "ANT_B", "VOUT", "GND", "LED_A", "CT1", "CT2", "CT3"):
        ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
    fps = {}
    for ref, (lib, name, val, pos, lcsc, fit) in PARTS.items():
        fp = pcbnew.FootprintLoad(str(lib), name)
        fp.SetFPID(pcbnew.LIB_ID("gg_card" if lib.name == "gg_card.pretty" else lib.name.replace(".pretty", ""), name))
        fp.SetReference(ref); fp.SetValue(val); fp.SetPosition(V(pos)); b.Add(fp)
        fp.Flip(fp.GetPosition(), True)
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        if lcsc: fp.SetProperty("LCSC", lcsc)
        if not fit: fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_DNP if hasattr(pcbnew, "FP_DNP") else fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
        fps[ref] = fp

    def pad(ref, num):
        p = fps[ref].FindPadByNumber(str(num)).GetPosition()
        return (pcbnew.ToMM(p.x) - G.OX, pcbnew.ToMM(p.y) - G.OY)
    def orient(ref, num, want):
        """Rotate the part by 180 deg if the given pad is not on the wanted side: want = ('x', +1) etc."""
        c = PARTS[ref][3]; p = pad(ref, num)
        d = (p[0] - c[0]) if want[0] == "x" else (p[1] - c[1])
        if d * want[1] < 0: fps[ref].SetOrientationDegrees(fps[ref].GetOrientationDegrees() + 180)
    fps["C2"].SetOrientationDegrees(90)
    orient("U1", 8, ("y", +1))          # LB towards the tuning bank, VOUT / VSS towards the LED
    orient("D1", 2, ("x", +1))          # anode on the R1 side
    orient("R1", 1, ("x", +1))
    orient("C2", 1, ("y", +1))          # pad 1 = VOUT (lower), pad 2 = GND (upper)
    for r in ("C3", "C4", "C5", "JP1", "JP2", "JP3"): orient(r, 1, ("x", -1))

    def setnet(ref, num, net): fps[ref].FindPadByNumber(str(num)).SetNet(nets[net])
    for ref, num, net in (("U1", 1, "ANT_A"), ("U1", 8, "ANT_B"), ("U1", 7, "VOUT"), ("U1", 2, "GND"),
                          ("R1", 1, "VOUT"), ("R1", 2, "LED_A"), ("D1", 2, "LED_A"), ("D1", 1, "GND"),
                          ("C2", 1, "VOUT"), ("C2", 2, "GND"),
                          ("C3", 1, "ANT_A"), ("C3", 2, "CT1"), ("JP1", 1, "CT1"), ("JP1", 2, "ANT_B"),
                          ("C4", 1, "ANT_A"), ("C4", 2, "CT2"), ("JP2", 1, "CT2"), ("JP2", 2, "ANT_B"),
                          ("C5", 1, "ANT_A"), ("C5", 2, "CT3"), ("JP3", 1, "CT3"), ("JP3", 2, "ANT_B")):
        setnet(ref, num, net)
    ant = [f for f in b.GetFootprints() if f.GetReference() == "ANT1"][0]
    ant.FindPadByNumber("1").SetNet(nets["ANT_A"]); ant.FindPadByNumber("2").SetNet(nets["ANT_B"])
    ant1 = ant.FindPadByNumber("1").GetPosition(); ant1 = (pcbnew.ToMM(ant1.x) - G.OX, pcbnew.ToMM(ant1.y) - G.OY)

    def track(net, pts, w=0.15, layer=pcbnew.B_Cu):
        for a, c in zip(pts, pts[1:]):
            if abs(a[0] - c[0]) + abs(a[1] - c[1]) < 1e-6: continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(a)); t.SetEnd(V(c)); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(nets[net]); b.Add(t)
    def via(net, p):
        v = pcbnew.PCB_VIA(b); v.SetPosition(V(p)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[net]); b.Add(v)

    u = {n: pad("U1", n) for n in range(1, 9)}
    r1v, r1l = pad("R1", 1), pad("R1", 2)
    dA, dK = pad("D1", 2), pad("D1", 1)
    c2v, c2g = pad("C2", 1), pad("C2", 2)
    XR, XBUS, XA, YB, YA = 68.1, 69.9, 62.4, 43.1, 48.75
    # harvested supply: VOUT -> 220n to ground, -> 47R -> LED
    track("VOUT", [u[7], (XR, u[7][1]), (XR, r1v[1]), r1v])
    track("VOUT", [(XR, c2v[1]), c2v])
    track("LED_A", [r1l, (dA[0], r1l[1]), dA])
    track("GND", [u[2], (dK[0], u[2][1]), dK])
    track("GND", [c2g, (c2g[0], V_G1[1]), V_G1]); via("GND", V_G1); via("GND", V_G2)
    track("GND", [V_G1, V_G2], layer=pcbnew.In2_Cu)
    track("GND", [V_G2, (dK[0], V_G2[1])])
    # antenna: outer end = ANT_A, inner end returns on layer 3 = ANT_B; three tuning capacitors behind solder bridges
    via("ANT_B", V_IN); via("ANT_B", V_B)
    track("ANT_B", [V_IN, V_B], 0.2, pcbnew.In2_Cu)
    track("ANT_B", [u[8], (u[8][0], YB), (XBUS, YB)], 0.2)
    track("ANT_B", [V_B, (XBUS, pad("JP3", 2)[1])], 0.2)
    track("ANT_A", [u[1], (65.2, u[1][1]), (65.2, YB), (XA, YB), (XA, YA), (ant1[0], YA), ant1], 0.2)
    for c, j, n in (("C3", "JP1", "CT1"), ("C4", "JP2", "CT2"), ("C5", "JP3", "CT3")):
        track("ANT_A", [(XA, pad(c, 1)[1]), pad(c, 1)], 0.2)
        track(n, [pad(c, 2), pad(j, 1)], 0.2)
        track("ANT_B", [pad(j, 2), (XBUS, pad(j, 2)[1])], 0.2)
    pcbnew.SaveBoard(str(dst), b)
    for ref in fps:
        print(ref, PARTS[ref][2], [(n.GetNumber(), round(pad(ref, n.GetNumber())[0], 2), round(pad(ref, n.GetNumber())[1], 2), n.GetNetname()) for n in fps[ref].Pads()][:8])

if __name__ == "__main__":
    main(HERE / "out" / "stage1.kicad_pcb", HERE / "out" / "hybrid_card_revA.kicad_pcb")
