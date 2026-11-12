# Prior-payment reconstruction and residual drift — November 12, 2026

Lifecycle: research development. User requested advancing EAD work. Status: executed
limited-coverage deterministic challenger and nonlinear drift diagnosis. Amortization
remains primary; no new baseline selection/approval/independent validation. Owner
institutional TBD. PD/LGD definitions and external frozen artifacts unchanged.

## Why the nonlinear model falls behind recently

On matched supported recent2023+ loans, needed aggregate schedule correction was
0.02138% at3months and0.06801% at12months. Frozen nonlinear model added0.08093% and
0.28106%, respectively. For2019–22, needed0.11968%/0.58466%,predicted0.11417%/0.55580%.
Quantities are SUM(actual-schedule) orSUM(predicted-schedule) divided bySUM(actual).
This diagnoses oversized corrections in the recent cohort, not a causal explanation
or an authorization to recalibrate to examined recent outcomes. Much of the recent
amortization error is already small; extra learned correction introduces positive bias.

## Prespecified payment-history method

Hypothesis: improve schedule reconstruction with strictly prior observed balances
rather than fitting another regression to contractual arithmetic. Four consecutive
monthly end balances ending at the anchor imply three prior payments:
P_t = B_(t-1)*(1+r/12)-B_t,with annual decimal rate r. Use median(P_t),only if
max(P_t)-min(P_t)<=max($1,0.1%*ABS(median(P_t))). Threshold and3month lookback
were stated in code before first results, not selected on recent errors.

With fixed rate and inferred payment, project principal using annuity recurrence.
Only Current/nonSDQ prior histories, fixed rate, no documented modification, same
rate/maturity, matching anchor balance, no prior balance increase, and a horizon
strictly before known maturity qualify. No history gaps or conflicting monthly keys.
Exclude ongoingIO/transition and lookbacks crossingIO end; retain frozen postIO
schedule or flagged hold there. Reject negative/exhausted projections, do not infer
balloon repayment. The payment is inferred from stated balances, not observed
cash receipts or proof of contract. Future outcome values do not enter reconstruction.
No global model fit or cohort-dependent coefficients.

## Results and coverage

Frozen primary reference reproduced exactly on all3867 horizon-case rows.
Reconstructions accepted111 of1915 three-month and115 of1952 twelve-month cases;
most otherwise-eligible histories fail the strict constant-payment/exhaustion check
(986/987). Keep rejected records with existing forecast, not remove them from score.
Recent acceptance only6 of418 three-month/four of454 twelve-month cases. Horizons
overlap; counts are not independent loans. No posthoc relaxation to force coverage.

Full initial-eligible error = SUM absolute dollar error / SUM actual scheduled UPB.

| Horizon/cohort | Cases | Existing routed reference | Prior-payment challenger |
|---|---:|---:|---:|
| 3m through2018 | 1002 | 0.16674% | 0.15166% |
| 3m2019–22 | 495 | 0.15369% | 0.14851% |
| 3m2023+ | 418 | 0.11093% | 0.10836% |
| 12m through2018 | 1018 | 0.74329% | 0.69669% |
| 12m2019–22 | 480 | 0.66909% | 0.66209% |
| 12m2023+ | 454 | 0.54619% | 0.54087% |

Gains are small recently:about2.3% relative error reduction3months,1.0%12months.
On supported advanced-matched recent cases,3m0.02264%to0.02256%(226),
12m0.19367%to0.19323%(250). These are distinct populations from full routed scores.
Do not claim this fixes the broad coverage gap or beats a complete economicEAD
model. Pre2019 rows are deterministic descriptive scores, not training-fit results.
Later periods previously examined; no independent generalization claim.

## Decision and remaining work

Retain the payment-history approach as a limited-coverage challenger, no wholesale
primary replacement. Structural payment reconstruction is supported where prior
balances genuinely exhibit stable payments, but current data do not identify a
constant payment for most cases under the prespecified rule. Investigate balance
reporting/payment timing and known contractual instruction availability before
relaxing gates or adding complexity. No inference of accrued interest, advances,
commitment draws or actual institution exposure from these principal forecasts.
SourceDefaultAmount/PD onset alignment remains unresolved. No automated EL.

## Artifacts, checks and change control

Final external immutable ead-payment-history-v0.1.1/report.json and predictions.parquet;
v0.1.0 retained initial diagnostic. Inputs include EADauditv0.2.0,advancedv0.1.1,
primary schedule-referencev0.1.0 and unchanged processed monthlyv0.3.0; report hashes
inputs and implementation,records routes,matched metrics and adjustment drift.
Old processed signed-loss parse limitation remains, no old signed loss fields used.

Reproduce python -m cre_expected_loss.models.ead_payment_history --root <Fannie-root>
--output <new-directory>. Tests recover a known payment and independently iterate
forward balances,zero-rate/IO cases,invalid history/instability and exhausted
schedule rejection. Frozen reference identity verified3867 rows; lint passes.
All loan-level/model artifacts outsideGit; initial manuscript unchanged locally.
Research branch ead-model-development. No source input overwritten. Rollback retains
checkpoint0d3b73c plus frozen primary models; new challenger additive only.

Verification November12:124 tests passed,five Pandoc-dependent skips;one existing
pandas deprecation warning. New module/test lint passes.
