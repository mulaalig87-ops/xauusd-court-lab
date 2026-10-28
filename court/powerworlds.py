"""G2b/G3 planted-law worlds: GARCH(1,1) returns with a small predictable drift.
The drift at bar t uses only information up to t-1 (a causal law)."""
import numpy as np


def planted(rng, T, law, beta, omega=0.02, a=0.08, b=0.90, burn=2000):
    n = T + burn
    z = rng.standard_normal(n)
    r = np.empty(n); s2 = omega / (1 - a - b); v = s2
    zbuf = np.zeros(n)                 # standardised past returns for the law
    lvl = 0.0; lv = np.zeros(n)
    regime_on = None
    if law == "L3":                    # persistent Markov regime, stay prob 0.995, ~50% on
        regime_on = np.empty(n); st = 1.0; u = rng.random(n)
        for t in range(n):
            if u[t] > 0.995:
                st = 1.0 - st
            regime_on[t] = st
    for t in range(n):
        sig = np.sqrt(s2)
        if t >= 70:
            if law in ("L1", "L3"):        # momentum on last 16 standardised returns
                g = np.tanh(zbuf[t - 16:t].sum() / 4.0)
                if law == "L3":
                    g *= regime_on[t]
            elif law == "L2":              # mean reversion of the 64-bar level z-score
                w = lv[t - 64:t]; sd = w.std() + 1e-12
                g = -np.tanh((lv[t - 1] - w.mean()) / sd)
            else:
                raise ValueError(law)
        else:
            g = 0.0
        r[t] = sig * (z[t] + beta * g)
        zbuf[t] = r[t] / sig
        lvl += r[t]; lv[t] = lvl
        s2 = omega + a * r[t] ** 2 + b * s2
    return r[burn:]
