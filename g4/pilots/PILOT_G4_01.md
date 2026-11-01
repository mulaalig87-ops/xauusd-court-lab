# G4 PILOT 01 — HHmax at longer horizons (exploratory, synthetic only; not evidence)

Code: `g4/pilot_h.py` (court and features unchanged except `build(r, H=...)` and `court_hh_max(..., H=H)`). T = 500,000, B = 9,999, seed root 707.
Calibration: N2/N3/N4 rotated, 400 worlds per H. Power: planted L1/L2 (`court/powerworlds.py`), 100 worlds per cell.

| H (M15 bars) | calib rej@.05 | calib rej@.01 | L1 β=.005 @.01 | L1 β=.01 @.01 | L2 β=.005 @.01 | L2 β=.01 @.01 |
|---|---|---|---|---|---|---|
| 4 (G3b, confirmed) | — | — | — | 0.807 | — | 0.957 |
| 16 (4 h) | 0.035 | 0.007 | 0.13 | 0.77 | 0.32 | 0.94 |
| 64 (16 h) | 0.048 | 0.007 | 0.03 | 0.15 | 0.10 | 0.68 |

Notes: calibration at longer H looks conservative-to-nominal on these worlds. Power for the *same planted per-bar law* falls at H=64 because the
planted laws (16/64-bar memory) are short-lived relative to the horizon; a G4 charter must define its power worlds and economic bar per horizon
(after costs), not reuse the per-bar β.
