# EAD schedule and LGD exposure-basis reconciliation — October 6, 2026

Lifecycle: research development. Status: executed evidence, not contract verification
or independent validation. User authorized continuation of amortization primary.
Institutional owner/approval TBD. Principal method remains deterministic schedule;
regression diagnostic only. No fitted models, definitions or frozen labels changed.

## Schedule convention evidence

Use the existing supported performing sample (22,045 overlapping windows), then
retain one latest supported window per loan:304 unique loans. This reduces
repeated-loan weighting but uses retrospective selection and is not untouched
validation or a representative whole-portfolio sample.

| Loan type | Unique loans | Calendar-age schedule error | Post-IO-clock error |
|---|---:|---:|---:|
| Amortizing balloon | 212 | 0.3290% | 0.3290% |
| Fully amortizing | 12 | 0.7324% | 0.7324% |
| Partial IO/amortizing/balloon | 79 | 0.5776% | 0.1928% |
| IO/balloon | 1 | 0.0000% | 0.0000% |

Error = total absolute predicted-principal difference / total observed scheduled
principal. Among64 loans whose convention predictions differ by more than one
cent, post-IO has lower error in all64; remaining loans have no material convention
difference. This supports provisional post-IO clock in this fixed-rate research
sample, not a claim that every Fannie contract follows that rule. Fully amortizing
sample12 is small, with90th absolute relative error6.791%; investigate residual
and month alignment before broadening. Both schedule conventions underpredict
sample aggregate principal; exact monthly payment instructions unavailable.

## Source LGD denominator identity and differences

Frozen signed LGD labels672 preserve source DefaultAmount; default_amount agrees
with parsed_default within1e-8 and signed_loss/parsed_default reconciles signed_ratio
within1e-12. No source parsing or denominator change in this step.

| Comparison to DefaultAmount | Positive matched cases | Equal within $0.01 | Source greater | Source smaller | Ratio within 1% |
|---|---:|---:|---:|---:|---:|
| Scheduled UPB at first SDQ | 660 | 82 | 420 | 158 | 597 |
| Participation Delinquency UPB at first SDQ | 633 | 418 | 28 | 187 | 565 |

Source DefaultAmount includes principal and accrued interest by glossary, whereas
current UPB is scheduled/stated principal and delinquency balance is Fannie's
participation. Different economic/reference dates and participation bases mean
DefaultAmount minus principal is NOT an identified accrued-interest amount.
Negative residuals158/187 rule out a universal nonnegative-interest add-on from
simple subtraction. Cures, redefaults, payment timing and data revisions remain
possible explanations, not established causes. Do not floor residuals or overwrite
source values.27 of660 positive scheduled cases lack positive participation balance;
12 of672 frozen LGD cases have no observed SDQ match.

First-SDQ to disposition gap660: median1.7495years,10th0.7849,90th3.6071; no negative
gaps. SDQ date is not source contractual default date. PD current proposed credit
event/disposition timing and EAD first-SDQ timing remain distinct definitions.

## Why immediate EL combination would change the loss basis

For source ratio L = reported signed loss / source DefaultAmount, multiplying L
by scheduled principal yields reported loss * (scheduled principal / DefaultAmount).
It does not reproduce the source dollar-loss identity unless bases agree.
Matched scheduled/source scale median0.998157,10th0.996663,90th1.007640; maximum
absolute departure66.48%. Participation/source scale median1.000000,10th1.000000,
90th1.009185,maximumdeparture66.93%. These are case-level algebraic scaling changes,
not portfolio bias or fitted EL errors; do not infer insignificant mismatch from
median alone. Preserve signed accounting identity and separate approximate economic
LGD target; latter contains additional cash-timing assumptions.

## Decision and next work

Retain post-IO reconstructed schedule as provisional principal research reference;
keep calendar convention as sensitivity and ridge diagnostic only. Evidence now
stronger than repeated-window totals, but no contract truth, point-in-time data
availability or production accuracy established. The chosen primary method does
not eliminate residual/default-basis uncertainty.

Keep EAD output explicitly principal-only and block automatic PD×LGD×EAD integration.
Next: date-aligned actual participation-balance target where observed; inspect
large denominator exceptions without clipping; evaluate whether a separate broader
exposure approximation is defensible. Source accrual/advance breakdown and contractual
default onset remain missing. Any new target or denominator is a separate research
version, not silent relabeling of the completed LGD baseline.

Reproduction: scripts/ead_schedule_reconciliation.py --artifact-root
<2026Q1-artifact-root> --output <new-directory>. External immutable
ead-schedule-reconciliation-v0.1.0 contains report.json,denominator_cases.parquet,
schedule_diagnostic_cases.parquet. Input hashes, one-to-one join and source loss
identity checks executed; no loan identifiers in Git documents. Lint passes.
Latest prior full suite110passed/five skips; this script adds aggregate evidence,
not a new core model or full-suite execution claim. Local uncommitted changes.
