# EAD research start — October 6, 2026

Lifecycle: model development. Status: completed field audit and initial benchmark,
not a fitted or selected EAD model, independent validation or production approval.
Audience: project developer/user/reviewer. Institutional owner and approval TBD.
Scope: Fannie multifamily public research, conditional exposure at a future event.
Implementation: scripts/ead_source_audit.py, parameterized external root/output.

## Definition and source evidence

Proposed principal benchmark outcome: scheduled/stated UPB at first observed
60+ payment status or SDQ Y. This is an observed delinquency proxy, not an approved
economic default definition or verified actual funded exposure. Exact 3/12-month
prior report anchors must be Current and not SDQ, with positive balances. Exclude
Credit Facility outcomes from benchmark scope; commitments/draws are not provided.
This is event-conditioned retrospective benchmarking, not an unconditional balance
forecast including payoff exits. The PD event implementation currently uses proposed
credit-event/disposition timing; do not combine these components until timing aligns.

The [Fannie glossary](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf),
March 2023, reviewed October 6, defines current UPB as scheduled/stated end-period
principal, Delinquency UPB as Fannie's participation at delinquency, and Default
Amount as principal plus accrued interest at default. Amortization Term, Original
I/O Term and I/O End Date support schedule research, but current standardized
monthly table omits them. Raw header verified. Separate accrued interest, advances,
commitment limits and draw schedules are absent. Missing components are not zero.
Original contract values and current rate do not establish revised payment schedules.

## Executed audit

External immutable artifact: ead-source-audit-v0.1.0 under the existing 2026Q1
artifact root. report.json records input SHA256 hashes and aggregate evidence;
benchmark_cases.parquet and lgd_denominator_reconciliation.parquet retain loan-level
rows outside Git. Inputs: immutable Multifamily.zip and frozen signed_outcomes.
No existing processed, LGD or PD artifact modified.

Raw projection: 5,392,800 rows, four repeated loan/date keys identical across all
selected EAD columns; deduplicated projected rows to 5,392,796. No conflicting
projected loan histories excluded. This establishes equivalence of selected
columns only, not full raw-row identity. 73,048 loans; no missing/negative current
UPB or missing reporting dates. Amortization Term missing in 87,829 monthly rows;
I/O end date present in 2,299,009; Delinquency UPB present in 26,852. Counts are
monthly-row counts, not independent loans. Product counts may overlap over history.

First observed SDQ: 2,120 loans; one has no preceding history. Includes cured and
unresolved cases; no resolved-loss restriction for principal benchmark. 660/672
signed LGD cases match first SDQ; remaining 12 have no matching observed onset.

| LGD denominator compared to onset balance | Positive matched | Median ratio | 10th/90th percentile ratio | Within 1% |
|---|---:|---:|---:|---:|
| Scheduled/stated current UPB | 660 | 1.001846 | 0.992418 / 1.003348 | 597 |
| Participation Delinquency UPB | 633 | 1.000000 | 0.990899 / 1.000000 | 565 |

These are descriptive comparisons across potentially different dates/bases.
Differences cannot be attributed solely to accrued interest, and ratios below
one must not be silently repaired. Investigate unmatched dates, cures/redefaults,
participation, amortization and source revisions. Do not replace LGD denominators.

## Initial balance-hold benchmark

Prediction is positive scheduled UPB at the earlier anchor, held constant.
No fitted parameters, macros, resampling or use of outcome fields as predictors.
Percentage below is SUM absolute dollar error / SUM observed onset scheduled UPB;
it is not average percentage error, accuracy or a confidence interval.

| Horizon | Onset period | Eligible cases | MAE dollars | Aggregate absolute error / outcome |
|---|---|---:|---:|---:|
| 3 months | Through 2018 | 1,002 | 16,364 | 0.3015% |
| 3 months | 2019–2022 | 495 | 37,218 | 0.3479% |
| 3 months | 2023 onward | 418 | 31,381 | 0.2647% |
| 12 months | Through 2018 | 1,018 | 64,652 | 1.2216% |
| 12 months | 2019–2022 | 480 | 143,126 | 1.3633% |
| 12 months | 2023 onward | 454 | 126,469 | 1.0594% |

These are descriptive chronological comparisons; onset-year periods differ from
LGD disposition-year partitions. Same loan can appear at both horizons; counts
must not be summed as independent cases. Larger exposures dominate the aggregate
metric; segment and tail diagnostics remain necessary. Later periods already
examined, not untouched tests. Current-status requirement excludes near-default
anchors and results do not generalize to every borrower/state. Revised public
snapshot and unverified publication dates preclude point-in-time claims.

## Next modeling work

Build an explicitly assumption-based amortization benchmark using original term,
I/O end, loan age, current note rate and current maturity; report coverage and
ambiguity before projecting. Payment schedule changes, balloons and past-maturity
defaults need separate treatment: a contractual maturity payment is not proof of
zero actual default exposure. Verify schedule against clean performing monthly
balance histories, then compare with hold baseline on identical eligible cases.
Audit participation/accrual differences separately. Fit a statistical residual
challenger only if schedule error and feature availability justify it. Macros are
not required by default for a deterministic contractual funded-balance benchmark.
Keep default horizon aligned with PD and denominator basis aligned with LGD before
expected-loss integration. Maintain whole-loan/institutional exposure distinction.

Verification: full raw audit executed, unique selected keys enforced after explicit
projection dedup, one-to-one frozen LGD join enforced, immutable output guard,
source hashes, saved aggregate report and lint. Existing EAD calculator tests
are run separately; audit adds no fitted-model or economic-EAD claim. Additive
research script/document only; rollback retains existing contractual EAD module.
