# EAD scheduled-principal research models — October 6, 2026

Lifecycle: model development. User authorized modeling. Status: two deterministic
schedule conventions and fixed ridge challenger executed; no baseline designation,
independent validation, institutional approval or EL deployment. Institutional owner
TBD. Population: Fannie multifamily, supported fixed-rate term-loan schedules before
maturity. Target is scheduled/stated principal at first observed 60+ delinquency,
not verified actual funded principal plus interest/advances at contractual default.
See ead_source_audit_2026-10-06.md for source glossary and initial audit.

## Models and dates

Balance-hold benchmark uses anchor UPB. Level-payment amortization uses current
anchor UPB, fixed current rate/1200, original amortization months, anchor loan age,
I/O end date and horizon. Assumes no new draws and no future rate/payment changes.
Primary convention remaining term at repayment start = amortization months minus
loan age minus remaining IO months. Sensitivity = amortization months minus elapsed
post-original-IO age. Both are assumed conventions, not verified contractual
payment instructions. Never turn an unpaid balloon into zero exposure: horizon at
or beyond anchor-known maturity is excluded and requires a separate model branch.
Modified, ARM, missing/invalid or exhausted terms also excluded from this candidate
comparison. I/O principal is held until end; remaining period uses annuity schedule.

Fixed ridge alpha 10 predicts onset/anchor UPB minus one; prediction is anchor UPB
times one plus predicted ratio. This directly targets arithmetic conditional mean
normalized balance, not a log/geometric mean. Six numeric predictors: schedule
fraction, loan age, note rate, remaining IO months, months to maturity, log anchor
UPB. StandardScaler fit only through-2018. Separate 3-month and 12-month models:
565 and 572 training cases. No tuning, clipping, resampling or macros. Nonfinite or
negative scored exposures fail explicitly; all saved predictions pass this check.
No automatic aggregation: broader exposure and PD/LGD definitions remain unresolved.

Anchor is exact 3/12-month earlier Current, non-SDQ report, with positive balances.
No realized balance is in predictor derivation. Outcome date provides the requested
horizon/end date. Raw revised public snapshot does not establish field availability
at historical execution date. Maturity/IO/contract backfills remain a limitation.
First SDQ uses all observed history and is not proof of first lifetime default.

## Matched comparisons

Aggregate error percent = total absolute dollar error / total observed principal,
not average percentage error or accuracy. All four candidates evaluated on the
same supported cases in each row. Through-2018 results are training fit, not
historical backtests. Later periods are now examined comparisons.

| Horizon | Onset period | Cases | Balance hold | Primary amortization | IO-clock sensitivity | Ridge |
|---|---|---:|---:|---:|---:|---:|
| 3 months | 2019–2022 | 306 | 0.4301% | 0.1797% | 0.1198% | 0.1051% |
| 3 months | 2023 onward | 226 | 0.3237% | 0.0710% | 0.0226% | 0.0908% |
| 12 months | 2019–2022 | 305 | 1.6439% | 0.8233% | 0.5850% | 0.3760% |
| 12 months | 2023 onward | 250 | 1.1729% | 0.3624% | 0.1937% | 0.3697% |

Supported coverage: 1,097/1,915 eligible three-month cases and 1,127/1,952 eligible
twelve-month cases from initial audit. Missing schedule inputs exclude 346/354;
at/beyond maturity 206/207; modified 127/130; nonfixed rate 115/109; invalid inputs
23/24; exhausted original term one each. Fixed-rate pre-maturity subset performance
must not be generalized to excluded loans. Horizons share loans and are not independent.

Schedule sanity check: deterministic DuckDB hash sample of loans, 43,488 candidate
12-month performing windows, 22,045 supported windows over 304 unique loans.
Both endpoints and observed intervening statuses Current/non-SDQ; same maturity,
rate and modification date; positive target and before observed SDQ. Windows
may overlap and are not independent. Clean-history selection is diagnostic, not
an operational prediction rule or independent test. Aggregate errors: hold1.4429%,
primary schedule0.8450%, IO-clock sensitivity0.7030%. Original schedule reconstruction
still has systematic underprediction; better errors do not prove contractual accuracy.

## Verification, artifacts and change control

Source audit ead-source-audit-v0.2.0 adds loan age, original IO and interest type,
and performing schedule samples without altering original v0.1.0 artifacts.
Immutable final model artifact: ead-research-v0.1.2, models.joblib,
predictions.parquet and report.json, all outside Git. Report hashes audit report
and both input tables. Saved pipelines reproduce all 2,224 matched predictions
within rtol1e-12/atol1e-8. Code: models/ead_amortization.py and ead_research.py.
Reproduce with python -m cre_expected_loss.models.ead_research --source
<ead-source-audit-v0.2.0> --output <new-output>.

Superseded diagnostic artifacts: v0.1.0 had an annuity formula missing growth
factor and a log-ratio ridge; do not use its results. v0.1.1 corrected annuity
but failed reload consistency while changing ridge transform; partial directory
is not a completed run. v0.1.2 corrects both, retains arithmetic mean target,
and passes independent annuity recursion and reload checks. Original files were
not overwritten. Additive research changes, original EAD calculator and frozen
LGD/PD checkpoints preserved. Code/docs remain local and uncommitted.

Tests cover annuity recursion, IO transition, zero rate, completion, invalid
inputs, predictor independence from realized outcome and maturity exclusion.
Next: inspect IO-clock convention against actual contract documentation and
performing residuals, expand missing/maturity/ARM coverage, run chronological
refit backtests and segment/tail diagnostics. Reconcile DefaultAmount principal,
accruals and participation separately before any combined EL result. Keep ridge
as a challenger; no candidate selected based solely on later comparisons.

Final verification: 107 tests passed, five Pandoc checks skipped; one existing
pandas deprecation warning. New EAD code/test lint passes.
