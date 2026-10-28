# xauusd-court-lab

Pre-registered calibration and power tests of a dependent-data hypothesis-testing court (HHmax: max-|t| over 10 causal
features with Hansen–Hodrick long-run variance), run entirely on **synthetic markets**. This repository contains
**no market data**.

- Charter (Arabic): `docs/G3B_CHARTER_v1.md`
- Court code (byte-identical to the frozen private versions): `court/`
- Runner, decision and anti-seed-fishing checks: `g3b/`
- Seeds come from a pre-committed drand quicknet round, verified with BLS (`g2/drand/verify.mjs`).
- Workflow: `.github/workflows/g3b-confirm.yml` (rehearsal on `rehearsal/**`, confirmatory on `main`).
