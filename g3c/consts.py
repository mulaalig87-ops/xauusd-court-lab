"""G3c constants (frozen with the charter)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "court"))
from worlds import n1_iid_t, n2_garch, n2b_garch_persistent, n3_regime, n4_garch_jumps, n5_seasonal  # noqa: E402
from release import CHARTER, WORKFLOW  # noqa: E402

LENGTHS = [376_275]                   # = INZO M15 bars (376,276) - 1 returns; fixed from the bar count only
B = 9_999
NULLS = [("N1", n1_iid_t), ("N2", n2_garch), ("N2b", n2b_garch_persistent),
         ("N3", n3_regime), ("N4", n4_garch_jumps), ("N5", n5_seasonal)]
W_NULL = 10_000
LAWS, BETAS, W_POWER = ["L1", "L2", "L3"], [0.005, 0.01, 0.015, 0.02, 0.03], 300
BAR_BETA = 0.015                      # G3c power bar (information ratio ~1.35/yr before costs)
EXPECTED_FEATURE = {"L1": "mom16", "L2": "zlevel64", "L3": "mom16"}
N_SHARDS = {"calib": 20, "power": 4}  # per length, confirmatory run (the workflow reads these)
STAGE = {"calib": 71, "power": 81}
PINNED = ["court/courts.py", "court/features.py", "court/worlds.py", "court/powerworlds.py",
          "g3c/consts.py", "g3c/release.py", "g3c/run_shard.py", "g3c/decide.py", "g3c/seed.py",
          "g3c/verify_anchor.py", WORKFLOW, "g2/drand/verify.mjs", "g2/drand/package.json",
          "requirements-lab.txt", CHARTER]


def tasks(mode):
    if mode == "calib":
        return [(i, w) for i in range(len(NULLS)) for w in range(W_NULL)]
    return [(c, w) for c in range(len(LAWS) * len(BETAS)) for w in range(W_POWER)]


def world(mode, li, cell, w, seed_base):
    """Deterministic world for (mode, length index, cell, w). Returns (returns, tag)."""
    from numpy.random import SeedSequence, default_rng
    from powerworlds import planted
    T = LENGTHS[li]
    wr = default_rng(SeedSequence(seed_base, spawn_key=(STAGE[mode], li, 0, cell, w)))
    if mode == "calib":
        return NULLS[cell][1](wr, T), NULLS[cell][0]
    law, beta = LAWS[cell // len(BETAS)], BETAS[cell % len(BETAS)]
    return planted(wr, T, law, beta), f"{law}_b{beta}"


def court_rng(mode, li, cell, w, seed_base):
    from numpy.random import SeedSequence, default_rng
    return default_rng(SeedSequence(seed_base, spawn_key=(STAGE[mode], li, 1, cell, w)))
