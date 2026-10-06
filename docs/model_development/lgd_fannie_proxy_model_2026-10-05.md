# Fannie discounted accounting proxy model — October 5, 2026

Lifecycle: model development. Status: fitted research model for an assumption-based approximation, not observed economic workout LGD or production-ready model. User authorized fitting. Original CPI signed-source baseline preserved; no new baseline designation or institutional approval inferred.

Implementation: models/lgd_proxy_model.py; CLI requires artifact-root, macro-root and output. Reuses fixed ridge alpha 10 and training-only preprocessing from the macro module. Fits numeric acquisition LTV, underwritten DSCR, log acquisition balance; categorical property type and loss-sharing type; optional six-month CPI log change. No realized workout duration, post-event proceeds or approximation value enters predictors. Actual feature date remains pre-disposition, potentially during workout: not an initial-default model.

Outcome source: external lgd-fannie-accounting-bridge-v0.1.0. Primary assumed target is 5% annual effective discount, terminal accounting net equivalent; stated before fitting, not optimized. Six rate/timing scenarios fitted for sensitivity. 660 unique eligible proxy cases; final fit uses 620 through-2018 cases, later comparisons 29 validation and 11 examined OOT. Missing-duration training cases not imputed; original 672-case eligibility unchanged. Four expanding chronological folds purge overlapping MBS groups, evaluating 606 cases. MBS is not verified borrower grouping. Historical evaluation includes the later validation years under their expanding-fold setup; do not add counts as independent evidence.

External immutable output lgd-fannie-proxy-model-v0.1.0: models.joblib, predictions.parquet, report.json. Inputs hashed; original source outcome and baseline not overwritten. CLI: python -m cre_expected_loss.models.lgd_proxy_model --artifact-root <2026Q1-artifact-root> --macro-root <CPI/CRE-snapshot-directory> --output <new-output>. Macro-panel helper reads both snapshots, but CRE is not a predictor. Saved model keys use rate/timing scope plus candidate; primary rate_0.05_timing_1_proxy_ridge_cpi.

## Primary comparison

MAE in loss-ratio percentage points, SAME approximated labels/populations for every candidate:

| Candidate | Historical 606 | Validation 29 | Examined OOT 11 |
|---|---:|---:|---:|
| Proxy training mean | 27.263 | 29.891 | 74.003 |
| Ridge fitted to proxy | 26.213 | 28.866 | 75.861 |
| Ridge+CPI fitted to proxy | 25.611 | 28.833 | 75.832 |
| Matched ridge+CPI fitted to signed source, scored against proxy | 26.619 | 28.081 | 76.365 |

CPI reduces primary proxy ridge historical MAE by 0.602 points; later CPI increment is tiny. Proxy refitting improves historical MAE versus source-trained comparator but worsens validation by 0.753 points. OOT error remains high and the mean benchmark is better on MAE; proxy ridge+CPI mean OOT prediction 41.733% versus mean proxy outcome 0.547%, demonstrating material mean overprediction. No overall superiority or model-selection claim follows.

## Sensitivity

Proxy ridge+CPI MAE:

| Assumed rate/timing | Historical | Validation | OOT |
|---|---:|---:|---:|
| 0%, terminal | 28.135 | 36.116 | 77.960 |
| 5%, midpoint | 26.757 | 31.830 | 76.896 |
| 5%, terminal (primary) | 25.611 | 28.833 | 75.832 |
| 10%, midpoint | 25.658 | 28.919 | 75.882 |
| 10%, terminal | 24.019 | 26.825 | 73.808 |

Targets differ across rows: lower error at a higher rate does not justify choosing that rate or establish better economic accuracy. Discounting mechanically shifts/compresses accounting net equivalents. Zero-rate midpoint equals terminal as required. No hyperparameter tuning, calibration, clipping or selection on validation/OOT. Preserve negative and above-one raw values.

## Verification and limitations

All three saved primary fitted pipelines reproduce their 40 later predictions after reload within absolute tolerance 1e-12. A synthetic test checks explicit target substitution, unchanged source frame and exclusion of duration/proxy columns from fitted feature names. Full suite 99 passed, five Pandoc checks skipped; one existing pandas deprecation warning. New lint passes.

Default/EAD/cash timing and cost/interest/allocation assumptions remain those of the bridge. Updated source labels and macro revisions prevent verified point-in-time claims. Event-year chronology is not proof of label availability. CPI lag is assumed. Future independent outcomes are not supplied. This estimates a conditional mean of an approximation at an existing during-workout prediction date. It does not establish actual economic LGD, causal macro effects, calibration for every sign group or suitability for EL use. Institutional loss versus whole-loan perspective still requires reconciliation.

No direct comparison of these errors to the original 672-case signed-target model is an improvement test. No automatic [0,1] bounded aggregation integration. Material change is an additive research outcome/model branch; rollback leaves original baseline in place. Current code/docs uncommitted, no checkpoint/push this turn. Next: model diagnostics by period/sign, onset/prediction-date alignment and source accounting reconciliation before baseline selection.
