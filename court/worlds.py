"""G2b synthetic null worlds (no directional structure), design stage.

Each generator returns log-returns r[0..T-1]. None contains predictable
direction; volatility may be predictable (that is baseline structure, not a law).
"""
import numpy as np


def n1_iid_t(rng, T, df=3):
    return rng.standard_t(df, T) / np.sqrt(df / (df - 2))


def n2_garch(rng, T, omega=0.02, a=0.08, b=0.90, burn=2000):
    z = rng.standard_normal(T + burn)
    r = np.empty(T + burn); s2 = omega / (1 - a - b)
    for t in range(T + burn):
        r[t] = np.sqrt(s2) * z[t]
        s2 = omega + a * r[t] ** 2 + b * s2
    return r[burn:]


def n2b_garch_persistent(rng, T):
    return n2_garch(rng, T, omega=0.005, a=0.08, b=0.915)


def n3_regime(rng, T, p_stay=0.995, ratio=3.0):
    state = np.empty(T, dtype=int); s = 0
    u = rng.random(T)
    for t in range(T):
        if u[t] > p_stay:
            s = 1 - s
        state[t] = s
    sig = np.where(state == 1, ratio, 1.0)
    return sig * rng.standard_normal(T) / np.sqrt((1 + ratio ** 2) / 2)


def n4_garch_jumps(rng, T, lam=0.005, jump_sd=6.0):
    r = n2_garch(rng, T)
    n = rng.poisson(lam, T)
    return r + n * rng.normal(0, jump_sd, T)


def n5_seasonal(rng, T, period=96, amp=1.0):
    t = np.arange(T)
    sig = 1.0 + amp * (0.5 + 0.5 * np.cos(2 * np.pi * t / period)) * 1.5
    return (sig / np.sqrt(np.mean(sig ** 2))) * n2_garch(rng, T)


# Nuisance-real (reported separately, NOT calibration): genuine lag structure.
def n6_bidask_bounce(rng, T, spread=0.3):
    latent = n2_garch(rng, T + 1)
    side = rng.choice([-1.0, 1.0], T + 1)
    obs = np.cumsum(latent) + spread / 2 * side
    return np.diff(obs)


CALIBRATION_WORLDS = {"N1": n1_iid_t, "N2": n2_garch, "N2b": n2b_garch_persistent,
                      "N3": n3_regime, "N4": n4_garch_jumps, "N5": n5_seasonal}
NUISANCE_WORLDS = {"N6": n6_bidask_bounce}
