# LGD loan-history research — October 5, 2026

Lifecycle: model development. Audience: model developers, owners and research reviewers. Status: exploratory research, no candidate selected or approved. Scope: Fannie Mae multifamily signed-source-ratio-v0.1.0, unchanged target and frozen baseline.

## Prediction dates and populations

Two distinct experiments avoid presenting workout information as default-onset information:

1. **Pre-disposition update:** existing latest monthly feature_date before source credit event; all 672 eligible loans. This may occur during workout, not at initial default. Four event-year chronological folds evaluate 615 loans; fixed later comparison uses 29 validation and 11 already-examined OOT loans.
2. **Before first observed serious delinquency:** last monthly report strictly before the first observed 60+ delinquency or SDQ indicator, if a preceding report exists. This is a retrospective evidence anchor, not an approved default definition. Covers 659 loans: 619 training, 29 validation, 11 OOT; 606 historical evaluation cases. Thirteen training loans lack qualifying anchor/history. Refit baselines on the same restricted population; do not compare its scores as if its sample were identical to the full population. The original baseline eligibility is unchanged.

The earlier anchor is typically much earlier than disposition: median 21.95 months. No observed serious delinquency lies at or before that anchor. Consequently, serious-delinquency duration predictors have no variation there; mild delinquency and history length can still vary. Source first_credit_event_date is disposition evidence, not approved default onset. Event-year splits are retained for comparability; they do not establish that resolved outcomes would have been available to an operational model at those historical dates.

## Features tested

All candidates retain acquisition LTV, underwritten DSCR, log acquisition UPB, property type and loss-sharing category. Incremental blocks:

- Lifecycle/collateral: seasoning from note date, months to recorded maturity, current balance/original balance, current note rate, rate-change indicator, property count, amortization type, interest type and lien position. Static audit fields are taken from earliest raw reporting records; require earliest record no later than anchor. No property sale prices or foreclosure valuations enter predictors.
- DSCR: exact reference-year historical DSCR, change versus preceding year and difference from underwritten DSCR. Conflicting annual loan/year values become missing, not averaged. Primary assumption uses anchor calendar year minus two; sensitivity uses minus one. Neither lag proves publication availability because annual publication dates are unavailable.
- Delinquency/history: latest and maximum preceding-12-month delinquency severity, share of observed preceding-12-month reports delinquent, observed SDQ-month count, months since first observed SDQ, observed history length and latest-report gap. These use only monthly rows at or before anchor. No lifetime ever-delinquent flag or post-event record enters the feature calculation.
- Combined: all three blocks. These experiments do not add macro variables; the earlier CPI experiment remains separate.

Missing numeric values use training-component medians, with explicit missing indicators. Entirely missing numeric component features use zero; their missingness remains explicit. Unknown categories remain Unknown. Fixed hyperparameters: ridge alpha 10, sign logistic C 0.1, Gamma alpha 10, zero probability training frequency. No tuning, caps, floors, class weighting, OOT calibration or automatic EL integration.

## Corrected experiment and retained diagnostic

External **lgd-history-research-v0.1.0** is diagnostic only. Its continuous note-rate minus original-rate feature was nearly constant in the earliest training period and generated unstable ridge extrapolations. Preserve it; do not use its models as the current history challenger.

External **lgd-history-research-v0.1.1** uses a simpler indicator for an absolute rate difference of at least 0.01 percentage point. Continuous differences remain in restricted features for diagnosis but are excluded from predictors. This is a development refinement after observed instability, not an independent confirmation. No predictions or outcomes were capped to hide the problem.

## Primary results: two-year DSCR lag

MAE in loss-ratio percentage points; lower is better.

| Pre-disposition candidate | Historical 615 | Validation 29 | Examined OOT 11 |
|---|---:|---:|---:|
| Ridge baseline | 28.640 | 35.671 | 79.214 |
| Ridge + lifecycle | 27.920 | 38.041 | 80.567 |
| Ridge + DSCR | 29.094 | 35.574 | 78.273 |
| Ridge + delinquency | 29.626 | 38.997 | 76.408 |
| Ridge + all history | 28.955 | 42.288 | 81.977 |
| Hurdle baseline | 29.520 | 37.313 | 76.726 |
| Hurdle + lifecycle | 29.264 | 36.888 | 77.685 |
| Hurdle + DSCR | 29.459 | 36.823 | 76.151 |
| Hurdle + delinquency | 29.622 | 36.971 | 76.829 |
| Hurdle + all history | 29.455 | 37.209 | 77.564 |

Lifecycle ridge improvement is 0.720 points, about 2.51% relative, but conditional paired 95% interval [-1.731, +0.348] includes zero. Its early-crisis fold improves 33.849 to 30.007; all three later folds worsen (24.776 to 25.209; 29.367 to 29.755; 35.671 to 38.041). This is not consistent improvement across time.

| Before-observed-SDQ candidate | Historical 606 | Validation 29 | Examined OOT 11 |
|---|---:|---:|---:|
| Ridge baseline | 28.739 | 36.158 | 78.013 |
| Ridge + lifecycle | 28.200 | 39.281 | 81.915 |
| Ridge + DSCR | 29.653 | 35.491 | 76.460 |
| Ridge + delinquency | 29.014 | 36.189 | 76.710 |
| Ridge + all history | 28.849 | 41.594 | 84.668 |
| Hurdle baseline | 29.660 | 37.516 | 77.155 |
| Hurdle + lifecycle | 29.359 | 37.597 | 78.009 |
| Hurdle + DSCR | 29.715 | 36.892 | 75.875 |
| Hurdle + delinquency | 29.555 | 37.036 | 76.308 |
| Hurdle + all history | 29.402 | 37.457 | 77.483 |

The larger combined model is not consistently better. Recent differences are exploratory on eleven cases; they are not a selection criterion. No unusual gain cases were removed or reclassified.

## DSCR timing sensitivity and missingness

Primary two-year-lag DSCR is missing in 253/672 pre-disposition loans and 274/659 earlier-anchor loans. DSCR change is missing in 360/672 and 399/659 respectively. This limits reliable estimation.

With one-calendar-year lag, historical ridge+DSCR MAE becomes 27.639 (full population) and 27.477 (earlier-anchor population), versus matched baselines 28.640 and 28.739. The apparent benefit depends materially on the assumed information date. Do not select the shorter lag from accuracy alone; obtain reporting/publication evidence first. Coefficients are conditional associations, not causal drivers or approved economic sensitivities.

## Reproduction, provenance and evidence

```powershell
python -m cre_expected_loss.models.lgd_history_research --fannie-root <external Fannie root> --output <new immutable artifact directory>
```

Inputs: frozen signed outcomes, earliest-record collateral allocation audit, processed v0.3.0 monthly history and annual DSCR. v0.3.0's known negative-loss parsing defect is not used for the target; signed outcomes remain from the reconciled event artifact. Raw and previous artifacts remain unchanged. report.json records input hashes, coverage, fold counts, aggregate scores, sign/magnitude diagnostics, conditional bootstrap intervals, runtime and limitations. features.parquet, predictions.parquet, models.joblib and ridge_coefficients.csv remain restricted external artifacts, never Git.

Verification reconciled all 615 refitted full-population ridge baseline predictions to the frozen baseline, and reloaded a saved hurdle model to reproduce all 29 validation predictions. Synthetic tests cover future-row exclusion, anchor timing, exact DSCR-year choice, conflicting annual values, duplicate monthly keys, invalid lags and train-only/component imputation. Test-suite results follow integration.

## Conclusion and next work

Available histories permit useful experiments; they do not yet establish a materially better overall LGD model. More features increase sparse-sample instability. Preserve simple baselines and avoid selecting by examined OOT outcomes. Prioritize actual annual DSCR availability evidence, approved default-onset/episode definitions, source loss finalization and extraordinary gain allocation. Keep pre-disposition update and earlier-history forecast uses distinct. True discounted economic LGD still needs dated cash flows and fuller collateral/security linkage; this signed source-ratio experiment does not supply them.

Source definitions: [Fannie Mae glossary](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf), [credit events and loss sharing](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-credit-loss-qrg.pdf).

Integrated verification: 82 passed, five existing Pandoc publication checks skipped. Ruff checks pass. One pandas deprecation warning arose in the synthetic future-row test; no calculation failure. No candidate selected or released.


Availability audit follow-up: Fannie announced public historical annual DSCR file introduction for late January 2021; no row-level publication dates exist in our source, and only raw release 2026Q1 is local. Most feature anchors precede 2021. See lgd_dscr_availability_2026-10-05.md. Neither reference-year lag establishes point-in-time public availability; internal lender receipt is a different information set.
