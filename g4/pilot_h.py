"""G4 PILOT (exploratory, synthetic only): HHmax calibration and power at longer horizons H.
usage: pilot_h.py MODE(calib|power) H T W PART NPARTS [LAW BETA]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "court"))
import numpy as np
from numpy.random import SeedSequence, default_rng
from courts import court_hh_max
from features_h import build
from worlds import n2_garch, n3_regime, n4_garch_jumps
from powerworlds import planted
mode, H, T, W, part, nparts = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
out = []
for w in range(part, W, nparts):
    rng = default_rng(SeedSequence(707, spawn_key=(H, T, w, 0 if mode == "calib" else 1)))
    if mode == "calib":
        r = [n2_garch, n3_regime, n4_garch_jumps][w % 3](rng, T)
    else:
        r = planted(rng, T, sys.argv[7], float(sys.argv[8]))
    F, names, Y = build(r, H=H)
    _, p, _ = court_hh_max(F, Y, 0.05, 9999, default_rng(SeedSequence(707, spawn_key=(H, T, w, 9))), H=H)
    out.append(p)
print(json.dumps({"mode": mode, "H": H, "T": T, "args": sys.argv[7:], "p": out}))
