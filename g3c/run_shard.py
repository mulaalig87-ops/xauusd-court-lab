"""G3c shard runner. usage: run_shard.py calib|power LENGTH_INDEX SEED_BASE SHARD N_SHARDS OUTDIR"""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "court"))
import numpy as np  # noqa: E402
from courts import court_hh_max  # noqa: E402
from features import build  # noqa: E402
from consts import B, LENGTHS, PINNED, court_rng, tasks, world  # noqa: E402

mode, li, seed_base, shard, n_shards, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), Path(sys.argv[6])
assert mode in ("calib", "power") and 0 <= li < len(LENGTHS) and 0 <= shard < n_shards
rows = []
for j, (cell, w) in enumerate(tasks(mode)):
    if j % n_shards != shard:
        continue
    r, tag = world(mode, li, cell, w, seed_base)
    F, names, Y = build(r)
    rej, p, tobs = court_hh_max(F, Y, 0.05, B, court_rng(mode, li, cell, w, seed_base))
    top = names[int(np.argmax(np.abs(court_hh_max.last_t)))]
    rows.append([cell, w, tag, p, float(tobs), top])
out.mkdir(parents=True, exist_ok=True)
hashes = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in PINNED}
blob = json.dumps({"mode": mode, "li": li, "T": LENGTHS[li], "seed_base": seed_base, "shard": shard, "n_shards": n_shards,
                   "numpy": np.__version__, "pinned_sha256": hashes, "rows": rows}, separators=(",", ":"))
(out / f"{mode}_L{li}_shard{shard:03d}.json").write_text(blob)
print(mode, li, shard, len(rows), hashlib.sha256(blob.encode()).hexdigest())
