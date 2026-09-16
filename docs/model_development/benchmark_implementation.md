---
title: "Fannie Mae Multifamily Benchmark Implementation Record"
status: "Development evidence — proposed, not approved"
version: "0.1.0"
as_of_date: "2026-09-10"
---

# Scope

This record describes the first executable model-development benchmark for the
Fannie Mae Multifamily Loan Performance Data 2026Q1 snapshot. It is research
evidence for economic expected-loss development only. It is not a validated or
approved model and is prohibited for production, CECL, capital, stress testing,
pricing, underwriting, or credit decisions.

# Implemented data transformation

The controlled transformation reads the two raw ZIP archives without modifying
them and creates versioned external Parquet tables. The monthly table contains
5,392,800 observations for 73,048 loans from January 2000 through March 2026.
The annual DSCR table contains 316,304 observations for 59,024 loans. No
reporting dates failed parsing, no current-UPB values were negative, and no loan
identifiers were missing.

The `fannie_outcomes_0.3.0` proposed PD outcome identifies each loan's first
reported credit-event date across its history and allocates the event to the
last observable monthly record on or before that date. It produces one event
for each of 765 loans with reported credit events. This allocation remains
subject to glossary review, record-level testing, and approval.

# Classical PD benchmark

The first benchmark estimates smoothed monthly hazards by property type and
five-year acquisition vintage. It uses observations through 2018 for training,
2019–2022 for temporal validation, and 2023–March 2026 as a reserved test period.
The smoothing strength of 500 observations is proposed and has not been tuned.

| Sample | Observations | Events | Predicted events | Observed/expected |
|---|---:|---:|---:|---:|
| Training | 3,111,250 | 663 | 664.46 | 0.998 |
| Temporal validation | 1,199,632 | 37 | 82.29 | 0.450 |
| Reserved test | 1,081,826 | 65 | 147.24 | 0.441 |

The later-period overprediction demonstrates material temporal instability.
This benchmark is therefore evidence for comparison, not a candidate for
approval in its current form. The final test result was calculated during this
initial benchmark implementation; consequently this partition must not be
described as untouched for subsequent selection unless a new prospective
holdout is defined.

# LGD and EAD benchmarks

Reusable functions now calculate the uncapped provisional ratio of lifetime net
credit loss to default amount and use current UPB as the ordinary fully funded
term-loan EAD benchmark. Neither definition is approved. LGD requires the loss
sharing guide, recovery timing, cost scope, seasoning, and unresolved-case
treatment. EAD requires event-date reconciliation, contractual amortization,
prepayment, modification, and facility-scope analysis.

# Classical discrete-time hazard candidate

A weighted logistic monthly hazard candidate was fitted using acquisition LTV,
underwritten DSCR, prior-calendar-year annual DSCR, note rate, loan age, log
current UPB, months to maturity, property type, state, amortization type, and
interest type. Every event was retained; non-events were selected by a
deterministic ten-percent hash sample and assigned inverse-probability weight.

| Sample | Weighted events | Weighted predicted events | O/E | ROC-AUC | Average precision |
|---|---:|---:|---:|---:|---:|
| Training | 663 | 669.02 | 0.991 | 0.948 | 0.01285 |
| Temporal validation | 37 | 137.76 | 0.269 | 0.820 | 0.00032 |
| Viewed test | 65 | 198.41 | 0.328 | 0.890 | 0.00092 |

The candidate separates risk but materially overpredicts later-period events.
Sparse events also make precision low. It requires temporal recalibration,
uncertainty analysis, macroeconomic features, point-in-time DSCR validation,
and comparison on a newly defined holdout before any selection decision.

# Next development gates

- Approve or revise the credit-event, exit, cure, and censoring definitions.
- Reconcile the 765 events to stratified record-level examples and source guides.
- Apply point-in-time annual DSCR availability rules and quantify missingness.
- Add macroeconomic vintages and a discrete-time hazard GLM primary candidate.
- Develop resolved-case LGD and event-date EAD samples before fitting severity models.
- Define a new final holdout before model selection because the current test metrics have been viewed.

# Macroeconomic candidate experiment

A dated FRED snapshot retrieved on September 16, 2026 contains unemployment,
the Chicago Fed National Financial Conditions Index, the 10-year Treasury
yield, the monthly Baa-to-Treasury spread, national rental vacancy, and rent
CPI. The monthly panel applies one-month lags to monthly, weekly, and daily
series and a two-month lag to quarterly rental vacancy. These are conservative
proposed availability rules. The snapshot contains latest-revised observations,
not historical vintages, so it is not yet point-in-time development evidence.

| Candidate | Validation O/E | Validation ROC-AUC | Validation log loss | Viewed-test O/E |
|---|---:|---:|---:|---:|
| No macro | 0.269 | 0.820 | 0.000389 | 0.327 |
| Labor | 0.550 | 0.820 | 0.000354 | 1.841 |
| Credit conditions | 0.213 | 0.823 | 0.000411 | 0.632 |
| Multifamily market | 0.332 | 0.822 | 0.000369 | 1.046 |
| Labor plus credit | 0.202 | 0.816 | 0.000431 | 1.784 |
| Labor plus multifamily | 0.285 | 0.811 | 0.000400 | 1.361 |
| All macro | 0.150 | 0.813 | 0.000486 | 1.276 |

The labor-only candidate is retained as the validation-selected macro
challenger because it provides the best validation calibration and log loss
without reducing discrimination. Its reversal to underprediction in the viewed
test period demonstrates regime instability. It is not selected as the primary
model. The near-one test O/E of the multifamily-market subset is diagnostic
only and cannot be used for selection because the test results have been viewed.

Required next work is vintage-aware retrieval, rolling-origin backtesting,
confidence intervals for sparse events, state-level unemployment, geographic
multifamily supply, and a newly defined prospective holdout.

## Vintage-aware implementation status

The repository now implements ALFRED `output_type=4`, which retrieves each
observation's initial release value. The API key is read only from the
`FRED_API_KEY` environment variable and is excluded from raw payloads,
manifests, logs, artifacts, and Git. The processed panel applies the same
documented reporting lags and is stored separately from latest-revised data.

Execution is pending a user-provided FRED API key. Until the initial-release
snapshot is downloaded and the labor challenger is rerun, the latest-revised
macro experiment remains diagnostic rather than point-in-time evidence.
