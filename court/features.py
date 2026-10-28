"""Causal candidate features and the baseline-standardised direction target."""
import numpy as np

H = 4                      # forecast horizon (bars)
LAM = 0.94                 # EWMA baseline volatility
WARM = 300                 # warm-up bars dropped


def ewma_sigma(r, lam=LAM):
    s2 = np.empty_like(r); v = np.var(r[:50])  # first 50 bars only seed the recursion
    for t in range(len(r)):
        s2[t] = v                     # sigma known BEFORE r[t] (uses r[:t])
        v = lam * v + (1 - lam) * r[t] ** 2
    return np.sqrt(s2)


def roll_sum(x, w):
    c = np.concatenate([[0.0], np.cumsum(x)])
    out = np.full(len(x), np.nan)
    out[w - 1:] = c[w:] - c[:-w]
    return out


def build(r):
    """Return (F [n x K], names, Y [n]). Row t uses r[:t+1] for features and
    r[t+1 .. t+H] for the target, standardised by sigma known at t+1."""
    T = len(r); sig = ewma_sigma(r)
    z = r / sig                                           # standardised past returns
    feats, names = [], []
    for w in (1, 4, 16, 64):
        feats.append(roll_sum(z, w) / np.sqrt(w)); names.append(f"mom{w}")
    for w in (4, 16, 64):
        feats.append(roll_sum(np.abs(z), w) / w); names.append(f"absz{w}")
    sgn = np.sign(r); run = np.zeros(T)
    for t in range(1, T):
        run[t] = run[t - 1] + 1 if sgn[t] == sgn[t - 1] and sgn[t] != 0 else 1
    feats.append(run * sgn); names.append("signed_run")
    lvl = np.cumsum(r); m = roll_sum(lvl, 64) / 64
    sd = np.sqrt(np.maximum(roll_sum(lvl ** 2, 64) / 64 - m ** 2, 1e-12))
    feats.append((lvl - m) / sd); names.append("zlevel64")
    feats.append(roll_sum(z, 16) / np.sqrt(16) - roll_sum(z, 64) / 8); names.append("mom16_minus_64")
    F = np.column_stack(feats)
    fwd = roll_sum(r, H)                                  # fwd[t+H] = sum r[t+1..t+H]
    Y = np.full(T, np.nan)
    Y[:T - H] = fwd[H:] / (sig[1:T - H + 1] * np.sqrt(H))  # sigma at t+1 uses r[:t+1]
    keep = np.arange(WARM, T - H)
    return F[keep], names, Y[keep]
