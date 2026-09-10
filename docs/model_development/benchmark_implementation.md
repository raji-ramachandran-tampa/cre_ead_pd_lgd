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

# Next development gates

- Approve or revise the credit-event, exit, cure, and censoring definitions.
- Reconcile the 765 events to stratified record-level examples and source guides.
- Apply point-in-time annual DSCR availability rules and quantify missingness.
- Add macroeconomic vintages and a discrete-time hazard GLM primary candidate.
- Develop resolved-case LGD and event-date EAD samples before fitting severity models.
- Define a new final holdout before model selection because the current test metrics have been viewed.
