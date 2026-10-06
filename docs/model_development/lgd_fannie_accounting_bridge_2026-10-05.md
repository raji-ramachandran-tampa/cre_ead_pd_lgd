# Fannie discounted accounting approximation — October 5, 2026

Status: user-authorized assumption-based approximation on the existing Fannie population; not observed economic workout LGD. No fitted economic model. CPI signed-source baseline remains unchanged.

Implemented models/lgd_accounting_bridge.py: proxy = 1 - (1 - signed source ratio)/(1+r)^(T*f). T uses first observed pre-event 60+ delinquency/SDQ to credit event disposition; f is 1 (terminal) or 0.5 (midpoint). Rates 0/5/10% are illustrative annual effective, ACT/365.25. First observed SDQ is not an approved default rule and may mix cured/redefaulted episodes. Terminal event dates are not proven receipt/finalization dates.

The numerator equivalent is source Default Amount minus reported net loss. It includes accounting expenses, foregone interest and benefits; it is not gross recovery. The denominator retains source Default Amount, not reconciled economic default EAD. This is an accounting bridge and can be interpreted as an economic-loss proxy only conditional on these assumptions. Do not add costs or benefits a second time. Net equivalents below zero (source ratios above one) are preserved, not relabeled negative gross cash receipts. At positive rates their modeled loss can decrease because a negative net equivalent is discounted. This is a mechanical consequence, not evidence of economic recovery behavior.

External immutable lgd-fannie-accounting-bridge-v0.1.0 has coverage.parquet, sensitivity.parquet and report.json. Uses frozen signed_outcomes and two-year-lag pre-disposition history features only to obtain preserved first_observed_sdq, hashes recorded. Unique loan/date coverage checked; DSCR values are not used for this target. No raw data overwritten; detailed rows outside Git.

Coverage: 660/672 have supported nonnegative duration; 12 missing-duration training cases receive no assumed duration. Original eligibility remains unchanged. Supported subset: 620 training, 29 validation, 11 examined OOT; median duration 1.749 years. Six scenarios per covered loan, 3,960 scenario rows, not independent observations.

Illustrative 5% terminal bridge, same covered population:

| Period | Loans | Mean signed ratio | Mean discounted accounting proxy | Mean shift, percentage points |
|---|---:|---:|---:|---:|
| Training | 620 | 38.591% | 44.151% | +5.560 |
| Validation | 29 | 18.950% | 32.061% | +13.111 |
| Examined OOT | 11 | -4.326% | 0.547% | +4.873 |

These are unweighted outcome averages, not prediction errors or evidence of better model performance. Do not compare the 620-loan mean to the original 632-training mean as if only discounting changed it. In the 5% terminal scenario, 45/5/5 negative proxies remain in training/validation/OOT and 15/2/2 proxies remain above one. No clipping or sign exclusion. No preferred rate or timing chosen from performance.

Verification: zero-rate rows reconcile to original signed ratios within 1e-12. Synthetic tests verify the equation, negative signs, above-one behavior and invalid durations. Final full suite 98 passed/five Pandoc checks skipped; one existing pandas deprecation warning. An initial existing-test rename failed in OneDrive; repeat outside synchronized storage passed after creating the test parent directory. New lint passes.

Next model stage must use matched supported cases, train-only preprocessing and observed-at-prediction features. Realized duration may construct retrospective targets but cannot be inserted as a prospective feature. Compare source-target and proxy-target models separately; cross-target MAE differences are not improvements. Missing finalization/vintages, default episode rule, interest accounting and loss perspective remain unresolved. No automatic bounded EL integration or institutional approval. Current research changes local/uncommitted.
