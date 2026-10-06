# CPI LGD working research baseline

## Current baseline decision — October 5, 2026

The user designated the full-population **ridge + CPI** model as the new working research baseline. This decision supersedes earlier "no candidate selected" statements for the working research reference only; no institutional selection, independent validation or production approval is implied. Original no-macro ridge and hurdle artifacts remain preserved comparators.

Current immutable external artifact: `lgd-cpi-baseline-v0.1.0`. It packages model key `0_ridge_cpi` from `lgd-macro-research-v0.1.0`, a selection manifest, source report and selected predictions. No refitting or validation/OOT calibration occurred. Train: 632 through-2018 outcomes. Features: acquisition LTV, underwritten DSCR, log acquisition UPB, property type, loss-sharing type and CPI six-month log change. Ridge alpha remains 10 with training-only preprocessing. Target remains the full signed source net-loss ratio.

MAE percentage points: historical 28.148 (615), validation 35.640 (29), examined OOT 79.161 (11). Historical gain versus original ridge is 0.492 points and concentrated in the early fold; later gain is negligible. CPI uses revised data and an assumed two-month publication lag, so point-in-time performance is unverified. Do not claim discounted economic LGD or automatically feed signed estimates into bounded EL aggregation.

Verification: saved selected model reproduces all 40 later predictions within absolute tolerance 1e-12. Prior full suite: 85 passed, five skipped. This designation changes the reference for subsequent experiments; historical reports retain their original comparison definitions. Current additions remain uncommitted; Git checkpoint/tag is pending. Use original artifacts to revert the working reference if needed.
