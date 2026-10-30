# First/last exposure alignment and common PD/EAD timing proposal — October 6, 2026

Lifecycle: research development. Status: completed sensitivity analysis and proposed
new research specification, not adopted default definition, independent validation,
institutional approval or integrated EL. User authorized comparison/proposal.
Institutional owner TBD. All frozen source/model definitions preserved.

## First-versus-last spell results

Frozen signedLGD672:660 have pre-resolution observed SDQ spells;66 have multiple,
61 existing training/five validation/zero existing OOT. Median first-to-last spell
start gap1.4949years,90th3.6687. Spells mean observed60+ status, not approved
contractual cure/redefault. No resolved-only population claim for PD/EAD.

| Basis, matched repeated-spell cases | Cases | First median absolute source scale difference | Last median absolute difference | Last closer / farther / equal | Last matches source within cent |
|---|---:|---:|---:|---|---:|
| Scheduled UPB | 66 | 1.3270% | 0.2542% | 49 / 12 / 5 | 9 |
| Participation UPB | 63 | 1.6634% | approximately0% | 48 / 6 / 9 | 32 |

Scale difference ABS(balance/DefaultAmount-1). First participation matched within
cent10, last32;3 cases lack paired positive participation. Similarity supports
resolution-linked timing mismatch as hypothesis, not proof of true default date.
Do not identify default by minimum exposure mismatch, floor differences into
interest or place last-spell information in initial predictors. Some later spells
fit worse; selection solely by closeness would introduce hindsight bias.

## Timing partition impact on frozen LGD cases

Existing partitions use source disposition/event year; proposed sensitivity uses
first observed SDQ year with the same2018/2022 cutoffs. Counts only, no refit:

| Existing cohort | First-SDQ through2018 | First-SDQ2019–22 | First-SDQ2023+ | No observed match |
|---|---:|---:|---:|---:|
| Training632 | 620 | 0 | 0 | 12 |
| Validation29 | 14 | 15 | 0 | 0 |
| Examined OOT11 | 0 | 8 | 3 | 0 |

Thus new onset-based cohorts would be634/23/3 matched outcomes, plus12 unmatched.
These are NOT the original620/29/11 duration-bridge cohorts and not extra
independent samples. Eight recent dispositions originate in earlier observed SDQ.
Onset chronology does not establish when final loss labels became available;
training must also exclude losses unresolved/unpublished by the fitting cutoff.
Do not retroactively claim the original comparison used common onset timing.

## Proposed next research specification

1. Observation/prediction date: a monthly report known at execution, with quarterly
   forecasting interface. Preserve economic report date separately from actual
   publication/availability date. Existing revised snapshot lacks full availability
   history; flag retrospective research and evaluate lag sensitivity.
2. PD event proxy: FIRST observed SDQY or60–89/90+ status after observed non-SDQ
   history. Stop the first-event risk set at that month. Loans already SDQ on first
   observed/gap-uncertain records are left-censored/uncertain, not new events with
   invented dates. Keep repayment/maturity exits and unresolved loans explicit.
3. EAD target for the same event: scheduled principal at that month, predicted from
   prior known schedules. Report participation at the same month as separate
   observed-institution exposure target/sensitivity. Three/twelve-month horizons
   are research evaluation points, not a complete quarterly term structure.
4. Repeated SDQ spells: retain an episode ledger for diagnostic/later-workout models.
   Return to non-SDQ is not automatically cure. A multi-state cure/redefault model
   requires a separate declared definition; do not count spells as independent loans.
5. LGD: preserve signed source loss/DefaultAmount baseline and discounted accounting
   approximation. Source losses may accrue across spells; final DefaultAmount date
   and episode attribution are unverified. Do not automatically assign aggregate
   source loss to first or last SDQ exposure. An onset-consistent LGD is a separate
   target version requiring label-availability and denominator reconciliation.
6. Integration: principal-onlyPD/EAD can share an observed proxy date after a new
   versioned PD experiment; existing disposition-based PD is unchanged. Economic
   PD×LGD×EAD remains disabled until common exposure basis and loss attribution
   justified. No automatic accrued-interest/advance estimate by subtraction.

This proposal distinguishes initial default-risk forecasting from resolution-
conditioned loss research. It is not an assertion of regulatory default alignment,
actual contractual default/cure identification or complete economic exposure.

## Next implementation gate

Create a SEPARATE first-SDQ PD experiment with explicit risk-set/censoring/outcome
availability audit; preserve previous PD artifacts. Audit all2,120 onset loans,
not only660 resolved labels. Produce a versioned event contract and report linkage
coverage to EAD and source LGD. No change of the original672 outcomes. Evaluate
quarterly hazard calibration on chronological cohorts with training-only fitting.
Keep target/denominator/date limitations explicit before any new combined EL.

Reproduction: scripts/ead_episode_alignment.py --artifact-root
<2026Q1-artifact-root> --output <new-directory>. External immutable
ead-episode-alignment-v0.1.0/report.json and linked_spell_cases.parquet. Input
SHA256, one-to-one joins, paired-positive coverage and all unmatched labels
retained. Code/run/lint checks pass. Latest existing suite113passed/five skips;
this is a new evidence script, not a new fitted model or full-suite execution.
No case IDs in Git documents. Local/uncommitted work, rollback leaves old models.
