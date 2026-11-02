# Advanced EAD schedule-residual challenger — November 2, 2026

Lifecycle: research development. User authorized implementation and GitHub update.
Branch ead-model-development. Status: fitted challenger, not selected primary,
independently validated, institutionally approved or production ready. Institutional
owner TBD. Existing amortization primary, guarded ridge, frozen LGD and PD retained.

## Declared target and method

Target declared before fitting: scheduled/stated UPB at first observed SDQ, same
as existing principal experiment. Residual y=(observed scheduled UPB-postIO schedule
forecast)/anchorUPB. Prediction=schedule+anchorUPB*predicted residual. No CCF,
participation target change, interest/advances approximation or economicEAD claim.

Shallow HistGradientBoostingRegressor (installed sklearn1.9.0), squared-error
mean loss. Fixed120iterations,learningrate.05,7leaves,maxdepth3,minleaf30,L2=1,
earlystoppingFalse,seed20261102. Six dated inputs: postIOschedule/anchor balance,
loanage,note rate,remainingIO,months to maturity,log anchor balance. No hyperparameter
search or later-period tuning. Guard scheduled principal to anchor balance for
entirelyIO horizons. Finite nonnegative point predictions required, no clipping.
Only supported fixed/unmodified/pre-maturity schedules, eligible Current anchors,
positive principal outcomes. Missing/maturity/ARM/modified fallbacks not extrapolated.

Mean models train through2018:565 three-month and572 twelve-month cases.
Loan-disjoint expanding historical folds train2008/test2009–11,2011/2012–14,
2014/2015–18,2018/2019–22. Ridge refitted on same training cohorts and guarded.
Historical evaluation754/766 includes2019–22 comparisons; do not add as independent
evidence. Borrower/MBS dependence not purged. Revised snapshot availability unverified.

## Matched point-model comparison

Aggregate error percent = total absolute dollar error / total observed principal.
All models in a row scored on identical supported cases. Counts overlap horizons.

| Horizon/cohort | Cases | PostIO amortization | Guarded ridge | Nonlinear residual |
|---|---:|---:|---:|---:|
| 3m historical refits | 754 | 0.0967% | 0.0727% | 0.0776% |
| 12m historical refits | 766 | 0.4727% | 0.2661% | 0.2160% |
| 3m2019–22 | 306 | 0.1198% | 0.0768% | 0.0811% |
| 12m2019–22 | 305 | 0.5850% | 0.2860% | 0.2170% |
| 3m2023 onward | 226 | 0.0226% | 0.0516% | 0.0619% |
| 12m2023 onward | 250 | 0.1937% | 0.2445% | 0.2154% |

Nonlinear residual helps historical twelve-month average errors, not uniformly
across horizons/tails. Recent amortization remains best on aggregate error. Recent
12m nonlinear bias+0.2130% of total outcome versus absolute error0.2154%, indicating
predominantly upward errors. Historical12m90th absolute relative error nonlinear
0.5973%,ridge0.4872%,schedule0.9251%: better aggregate MAE is not every-tail superiority.
No baseline replacement justified. These are scheduled-principal errors, not full
economic exposure performance, and cannot be compared with full-eligible routed
error0.5462% as if samples matched. Later cohorts already examined.

## Quantiles and temporal calibration

Separate05/95 quantile residual models fit only through2014 (454/457). Calibration
2015–18 (111/115), no refit on calibration/later outcomes. Calibration score is
max(lower-y,y-upper,0)/anchor; use ceil((n+1)*.9) order statistic for nominal90%
expansion. Quantile crossing handled by explicit min/max envelope; raw later
crossings zero. Lower bounds intersect nonnegative exposure domain. EntireIO
principal bounds fixed to anchor under no-draw/capitalization assumption.
Mean model and quantile model have different declared training cutoffs. Quantile
midpoints are not substituted for mean EAD. No coverage guarantee under time drift.

| Horizon/cohort | All supported coverage | NonIO coverage | NonIO cases |
|---|---:|---:|---:|
| 3m2019–22 | 94.44% | 93.49% | 261 |
| 12m2019–22 | 93.44% | 92.31% | 260 |
| 3m2023 onward | 89.38% | 85.63% | 167 |
| 12m2023 onward | 92.40% | 89.08% | 174 |

IO deterministic zero-width cases inflate overall coverage relative to amortizing
loans. Recent nonIO3m range undercovers nominal90%; twelve-month near90%, not proof
of calibrated tails. No posthoc widening based on these examined later outcomes.
Residual distribution drift and segmentation need assessment before risk use.

## Verification, provenance and reproduction

Final immutable external artifact ead-advanced-residual-v0.1.1:models.joblib,
predictions.parquet,historical_predictions.parquet,report.json. Source
benchmark/audit and implementation SHA256,installed sklearn and fixed parameters
recorded. Final later mean and both interval bounds reload-match1087 horizon-case
predictions withinrtol1e-12/atol1e-8. Initialv0.1.0 retained as diagnostic; v0.1.1
adds explicit IO point guard, source-code hash, interval validation and nonIO
coverage diagnostics. No original data/model artifact overwritten.

Code models/ead_advanced.py; CLI requires --source <ead-source-audit-v0.2.0>
--output <new-directory>. OMP_NUM_THREADS=2 used for bounded execution; no package
upgrade. Synthetic tests cover conformal order statistic/insufficient sample,
invalid scores/radius, quantile crossing/IO rule, evaluator-outcome independence,
loan overlap and chronological contracts. Full suite result recorded in restart
handoff. No loan-level records or serialized models enter Git.

Decision: amortization remains primary. Nonlinear and guarded ridge stay diagnostic
challengers. Next work should investigate schedule reconstruction and residual
stability/interval undercoverage, not tune on already examined recent cohorts.
CCF, full economicEAD and integratedPD/LGD/EAD remain unsupported without the
previously documented exposure/date/denominator evidence. No PD refit or LGD
relabeling in this change. Rollback uses d6fbefd and preserved EAD reference.

Verification completed November2:117 tests passed,five Pandoc-dependent skips;
one pre-existing pandas deprecation warning. New code/test lint passes.

Method reference: Romano,Patterson,Candes(2019),Conformalized Quantile Regression,
https://arxiv.org/abs/1905.03222. This implementation uses a nonnegative-score
expansion and explicit IO guard; temporal data do not establish exchangeability
or a guaranteed coverage result. Empirical coverage is reported above.
