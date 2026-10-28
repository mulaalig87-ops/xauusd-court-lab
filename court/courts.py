"""Candidate dependent-data courts. Each returns (reject: bool, p: float, stat: float).
Statistic: max_k |corr(F_k, Y)| over the candidate family (selection inside resamples)."""
import numpy as np
from scipy.stats import norm


def _std(A):
    A = A - A.mean(0); return A / np.sqrt((A ** 2).sum(0))


def court_cs(F, Y, alpha, B, rng, min_shift=500):
    """Circular shift of Y against F (FFT cross-correlation for all shifts)."""
    Fs, ys = _std(F), _std(Y[:, None])[:, 0]
    n = len(ys)
    fy = np.fft.rfft(ys)
    cc = np.fft.irfft(np.conj(np.fft.rfft(Fs, axis=0)) * fy[:, None], n=n, axis=0)  # cc[s,k]=sum_t F[t,k]*y[t+s]
    obs = np.abs(cc[0]).max()
    shifts = rng.integers(min_shift, n - min_shift, B)
    null = np.abs(cc[shifts]).max(1)
    p = (1 + (null >= obs - 1e-12).sum()) / (B + 1)
    return p <= alpha, p, obs


def _sb_indices(rng, n, L):
    idx = np.empty(n, dtype=np.int64); i = rng.integers(n)
    for t in range(n):
        idx[t] = i
        i = rng.integers(n) if rng.random() < 1.0 / L else (i + 1) % n
    return idx


def court_sbmax(F, Y, alpha, B, rng, L=50):
    """Stationary bootstrap of (F,Y) pairs, max-|t| with centering (single-step
    Romano-Wolf / Reality-Check style). Studentised by bootstrap SD per candidate."""
    Fs = _std(F); ys = _std(Y[:, None])[:, 0]
    n = len(ys); obs_c = Fs.T @ ys
    boots = np.empty((B, Fs.shape[1]))
    for b in range(B):
        ix = _sb_indices(rng, n, L)
        fb, yb = F[ix], Y[ix]
        boots[b] = _std(fb).T @ _std(yb[:, None])[:, 0]
    sd = boots.std(0, ddof=1)
    tobs = np.abs(obs_c / sd).max()
    tnull = np.abs((boots - obs_c) / sd).max(1)
    p = (1 + (tnull >= tobs).sum()) / (B + 1)
    return p <= alpha, p, tobs


def court_hac_bonf(F, Y, alpha, B=None, rng=None, lags=None):
    """Newey-West t for each slope of Y on standardised F_k, Bonferroni over K."""
    n, K = F.shape; lags = lags or int(4 * (n / 100) ** (2 / 9)) + 4
    ps = []
    for k in range(K):
        x = (F[:, k] - F[:, k].mean()) / F[:, k].std(); y = Y - Y.mean()
        beta = (x @ y) / (x @ x); e = (y - beta * x) * x
        s = e @ e
        for l in range(1, lags + 1):
            s += 2 * (1 - l / (lags + 1)) * (e[l:] @ e[:-l])
        se = np.sqrt(s) / (x @ x)
        ps.append(2 * norm.sf(abs(beta / se)))
    p = min(1.0, min(ps) * K)
    return p <= alpha, p, min(ps)


COURTS = {"CS": court_cs, "SBmax": court_sbmax, "HACbonf": court_hac_bonf}


def court_cs_sn(F, Y, alpha, B, rng, min_shift=500):
    """Circular shift with self-normalised (heteroskedasticity-robust) statistics:
    t_k(s) = sum_t x_k(t) y(t+s) / sqrt(sum_t x_k(t)^2 y(t+s)^2). Robust to volatility
    alignment between features and target, which plain CS breaks under the null."""
    X = F - F.mean(0); y = Y - Y.mean(); n = len(y)
    fy, fy2 = np.fft.rfft(y), np.fft.rfft(y * y)
    num = np.fft.irfft(np.conj(np.fft.rfft(X, axis=0)) * fy[:, None], n=n, axis=0)
    den = np.fft.irfft(np.conj(np.fft.rfft(X * X, axis=0)) * fy2[:, None], n=n, axis=0)
    t = np.abs(num) / np.sqrt(np.maximum(den, 1e-300))
    obs = t[0].max()
    shifts = rng.integers(min_shift, n - min_shift, B)
    null = t[shifts].max(1)
    p = (1 + (null >= obs - 1e-12).sum()) / (B + 1)
    return p <= alpha, p, obs


COURTS["CS_SN"] = court_cs_sn


def court_hh_max(F, Y, alpha, B, rng, H=4):
    """Martingale-difference court. Under H0 (returns unpredictable from the past),
    z_t = x_t * y_t has E[z_t | F_t] = 0 and is uncorrelated beyond lag H-1, whatever
    the volatility dynamics. Long-run covariance by Hansen-Hodrick (uniform weights,
    lags 0..H-1, PSD-clipped); p-value of max_k |t_k| by Gaussian simulation (B draws)
    that keeps the cross-candidate correlation. Asymptotically valid, not exact."""
    X = (F - F.mean(0)) / F.std(0); y = Y - Y.mean(); n = len(y)
    Z = X * y[:, None]
    Om = Z.T @ Z / n
    for l in range(1, H):
        G = Z[l:].T @ Z[:-l] / n; Om += G + G.T
    w, V = np.linalg.eigh(Om); Om = (V * np.maximum(w, 1e-12 * w.max())) @ V.T
    se = np.sqrt(np.diag(Om) / n)
    tvec = Z.mean(0) / se
    court_hh_max.last_t = tvec
    tobs = np.abs(tvec).max()
    C = Om / np.outer(np.sqrt(np.diag(Om)), np.sqrt(np.diag(Om)))
    L = np.linalg.cholesky(C + 1e-12 * np.eye(len(C)))
    sims = np.abs(rng.standard_normal((B, len(C))) @ L.T).max(1)
    p = (1 + (sims >= tobs).sum()) / (B + 1)
    return p <= alpha, p, tobs


COURTS["HHmax"] = court_hh_max
