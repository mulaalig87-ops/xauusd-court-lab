"""G3b decision (charter sections 4-6).
usage: decide.py SHARD_DIR N_CALIB_SHARDS N_POWER_SHARDS SEED_BASE
Per length T: G2b (calibration) and G3 (power), each PASS / FAIL / INCOMPLETE."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "court"))
from scipy.stats import beta, binom  # noqa: E402
from consts import B, BETAS, EXPECTED_FEATURE, LAWS, LENGTHS, NULLS, PINNED, W_NULL, W_POWER, court_rng, world  # noqa: E402
from release import FREEZE  # noqa: E402

d, nsh, sb = Path(sys.argv[1]), {"calib": int(sys.argv[2]), "power": int(sys.argv[3])}, int(sys.argv[4])
FZ = ROOT / FREEZE
if FZ.exists():   # confirmatory or rehearsal: the tree must equal the freeze
    subprocess.check_call(["git", "-C", str(ROOT), "diff", "--quiet", json.loads(FZ.read_text())["freeze_sha"], "HEAD", "--", ".", f":!{FREEZE}"])
expect_hash = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in PINNED}
LEV = 0.01 / 12
CAP = {0.05: 625, 0.01: 125}


def recheck(mode, li, rows, k=12):
    from numpy.random import SeedSequence, default_rng
    from courts import court_hh_max
    from features import build
    pick = default_rng(SeedSequence(sb, spawn_key=(98, li, {"calib": 41, "power": 51}[mode]))).choice(len(rows), size=min(k, len(rows)), replace=False)
    bad = 0
    for i in pick:
        cell, w, tag, p = rows[i][:4]
        r, _ = world(mode, li, cell, w, sb)
        F, _, Y = build(r)
        _, p2, _ = court_hh_max(F, Y, 0.05, B, court_rng(mode, li, cell, w, sb))
        bad += int(p2 != p)
    return bad


res = {"seed_base": sb, "lengths": {}}
for li, T in enumerate(LENGTHS):
    R = {"G2b": {"status": "PASS", "problems": [], "cells": {}}, "G3": {"status": "PASS", "problems": [], "cells": {}}}
    data = {"calib": [], "power": []}
    for mode, gate in (("calib", "G2b"), ("power", "G3")):
        for s in range(nsh[mode]):
            f = d / f"{mode}_L{li}_shard{s:03d}.json"
            if not f.exists():
                R[gate]["problems"].append(f"missing {f.name}"); continue
            m = json.loads(f.read_text())
            if (m["seed_base"] != sb or m["n_shards"] != nsh[mode] or m["shard"] != s or m["li"] != li
                    or m["T"] != T or m["mode"] != mode or m["pinned_sha256"] != expect_hash):
                R[gate]["problems"].append(f"integrity {f.name}"); continue
            data[mode] += m["rows"]
        ncell = len(NULLS) if mode == "calib" else len(LAWS) * len(BETAS)
        wmax = W_NULL if mode == "calib" else W_POWER
        if any(not (0 <= r[0] < ncell and 0 <= r[1] < wmax) for r in data[mode]):
            R[gate]["problems"].append("row key out of range")
        keys = [(r[0], r[1]) for r in data[mode]]
        if len(keys) != len(set(keys)):
            R[gate]["problems"].append("duplicate rows")
        if len(set(keys)) != ncell * wmax:
            R[gate]["problems"].append(f"have {len(set(keys))} of {ncell * wmax}")
        if R[gate]["problems"]:
            R[gate]["status"] = "INCOMPLETE"
        elif data[mode]:
            nb = recheck(mode, li, sorted(data[mode]))
            R[gate]["recheck_mismatches"] = nb
            if nb:
                R[gate]["problems"].append(f"{nb} recomputed rows differ"); R[gate]["status"] = "INCOMPLETE"
    for i, (name, _) in enumerate(NULLS):
        ps = [r[3] for r in data["calib"] if r[0] == i]; n = len(ps)
        for a in (0.05, 0.01):
            k = sum(p <= a for p in ps)
            p_infl = float(binom.sf(k - 1, n, 1.1 * a)) if n else 1.0
            fail = n == W_NULL and (p_infl <= LEV or k > CAP[a])
            R["G2b"]["cells"][f"{name}@{a}"] = {"n": n, "k": k, "rate": k / max(n, 1), "p_inflation": p_infl,
                "cp95": [float(beta.ppf(.025, k, n - k + 1)) if k else 0.0, float(beta.ppf(.975, k + 1, n - k))] if n else None,
                "fail": bool(fail)}
            if fail and R["G2b"]["status"] == "PASS":
                R["G2b"]["status"] = "FAIL"
    for c in range(len(LAWS) * len(BETAS)):
        law, b = LAWS[c // len(BETAS)], BETAS[c % len(BETAS)]
        rows = [r for r in data["power"] if r[0] == c]; n = len(rows); hits = [r for r in rows if r[3] <= 0.01]
        R["G3"]["cells"][f"{law}_b{b}"] = {"n": n, "power@.05": sum(r[3] <= 0.05 for r in rows) / max(n, 1),
            "power@.01": len(hits) / max(n, 1), "attribution@.01": sum(r[5] == EXPECTED_FEATURE[law] for r in hits) / max(1, len(hits))}
    if R["G3"]["status"] == "PASS":
        for law in ("L1", "L2"):
            if R["G3"]["cells"][f"{law}_b0.01"]["power@.01"] < 0.8:
                R["G3"]["status"] = "FAIL"
    R["gold_entry_allowed_at_this_T"] = R["G2b"]["status"] == "PASS" and R["G3"]["status"] == "PASS"
    res["lengths"][str(T)] = R
print(json.dumps(res, indent=1))
(d / "G3B_RESULT.json").write_text(json.dumps(res, indent=1))
for T, R in res["lengths"].items():
    for g in ("G2b", "G3"):
        brief = {k: (v["k"] if g == "G2b" else round(v["power@.01"], 3)) for k, v in R[g]["cells"].items()}
        print(f"::notice title=T{T}-{g}-{R[g]['status']}::" + json.dumps(brief)[:950])
