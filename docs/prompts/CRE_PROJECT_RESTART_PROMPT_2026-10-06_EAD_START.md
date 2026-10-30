# CRE restart — October 6, 2026: LGD checkpoint and EAD start

Status: current research handoff. Audience: developer, user and future reviewer.
Owner: institutional owner TBD. User authorized GitHub checkpoint and transition
to EAD. No independent validation, institutional approval or production release.
Read AGENTS.md, CRE_PROJECT_META_PROMPT.md and tasks/model_development.md.
This supersedes the October 5 restart for current state; retain that document
and linked reports as historical evidence.

## Current EAD method decision — October 6, 2026

User agreed deterministic contractual amortization is the primary research method;
guarded ridge is diagnostic challenger only. This supersedes older no-primary
statements at method level, not institutional model approval. See
model_development/ead_primary_method_2026-10-06.md and config/ead_research.yaml.
External ead-schedule-reference-v0.1.0 freezes the prior routed predictions with
basis/verification flags; IO-clock reconstruction remains provisional, maturity
and unknown schedules retain flagged holds, no new performance claim. No verified
contract/actual broad EAD, PD/LGD integration or independent validation. Git
checkpoint pending. Next: schedule-convention verification and actual/scheduled
principal, accrual, participation and default-date reconciliation.

## LGD decisions and evidence

LGD research development is complete for this phase, with limitations retained.
Working baseline: full signed source net-loss ratio, ridge alpha 10 + six-month
CPI log change, training-only preprocessing. Preserve negative and above-one
outcomes. Original no-macro and signed hurdle comparators remain available.

Signed baseline: 632 training, 29 validation, 11 examined out-of-time cases.
Historical expanding-fold evaluation: 615 cases. MAE in percentage points:
28.148 historical, 35.640 validation, 79.161 examined out-of-time.
External immutable artifact: lgd-cpi-baseline-v0.1.0.
See ../model_development/lgd_cpi_baseline_2026-10-05.md.

Discounted accounting approximation: separate experimental branch, primary
illustrative 5% annual effective rate with terminal timing. Formula:
1 - (1 - signed source ratio) / (1 + rate) ** duration_years.
Source DefaultAmount is not verified economic EAD; inferred net recovery is
an accounting equivalent, not an observed cash-flow ledger. First observed
serious delinquency and disposition supply assumed timing. Costs, interest and
allocation benefits may already be embedded. No extra deduction or sign clipping.

Proxy fit: 620 training, 29 validation, 11 examined out-of-time; historical606.
Ridge+CPI MAE: 25.611 / 28.833 / 75.832 percentage points. Mean benchmark
out-of-time MAE 74.003, better than fitted ridge. Recent performance remains
weak. Changed targets and samples preclude direct improvement claims against
the original signed baseline; discount rates must not be chosen by MAE.
External artifacts: lgd-fannie-accounting-bridge-v0.1.0 and
lgd-fannie-proxy-model-v0.1.0. See the corresponding October 5 development reports.

Two public CMBS resolved-case studies verify source arithmetic and sensitivities;
they are not a fitted sample or complete observed economic workout ledgers.
No pooling with Fannie, no selected economic proxy baseline, no EL integration.

## Reproduction and restrictions

Fannie raw release 2026Q1; monthly v0.3.0 remains unreconstructed after the
accounting-parenthesis parser correction. Signed labels independently reconcile
raw histories. External artifacts and inputs remain outside Git, with manifests
and input hashes. Resolve paths through existing configuration; inspect reports
before reuse. Repository contains code, synthetic tests and aggregate evidence.

Latest LGD verification: 99 tests passed, five Pandoc-dependent checks skipped;
one existing pandas deprecation warning. Saved primary proxy pipelines reproduce
40 later predictions within absolute tolerance 1e-12. Historical and examined
later periods are development evidence, not independent validation. Revised CPI
and assumed publication lag do not establish point-in-time performance.
Prediction features may be during workout, not known at initial default.
Current checkpoint tag: cre-lgd-to-ead-2026-10-06; resolve its Git commit for code.
Older 'uncommitted' statements describe earlier task status, superseded here.
Rollback: retain frozen original baseline artifacts and prior Git checkpoint
cre-lgd-research-2026-10-05; do not overwrite external artifacts.

## Start EAD here

Requested next work: EAD research development for Fannie multifamily within the
CRE expected-loss framework. EAD estimation is not yet completed by this handoff.
Existing src/cre_expected_loss/models/ead.py provides a tested contractual
balance benchmark from scheduled principal and explicitly supplied future draws.
It is not an empirical Fannie EAD model or a verified contractual schedule.

1. Inspect existing PD/default definitions, EAD code, data dictionary and raw
   monthly balance/contract fields. Record what is observed versus unavailable.
2. Propose consistent prediction date, quarterly horizon, default onset, units
   and exposure basis. Reconcile source DefaultAmount with balance at default
   and with signed/proxy LGD denominators; quantify unmatched cases.
3. Establish contractual funded-balance/amortization benchmark with interest-only
   and balloon treatment supported by actual fields. Keep prepayment, maturity,
   modifications and future funding explicit; no fabricated commitments/draws.
4. Compare predicted versus observed exposure at eligible default dates with
   chronological partitions and training-only fitting; prevent post-default
   information leakage. Decide whether a statistical challenger adds value.
5. Document missing interest/advances/cash flows, denominator reconciliation,
   tests, artifacts and limitations before combining PD, LGD and EAD.

Open decisions: default onset, prediction horizon, funded-principal versus
broader exposure, accrual/advance coverage, loan/whole-loan perspective and
prospective data availability. Preserve LGD outcome definitions while auditing;
do not silently replace denominators or feed signed outputs into bounded EL.

## EAD field audit executed — October 6, 2026

See docs/model_development/ead_source_audit_2026-10-06.md and external
ead-source-audit-v0.1.0. Raw field audit and flat scheduled-balance benchmark
completed: 2,120 first observed SDQ loans; 660/672 LGD cases match onset, 597 of
660 DefaultAmount/scheduled-UPB ratios within 1%. Three-month benchmark aggregate
absolute error/outcome about 0.265–0.348%, twelve-month 1.059–1.363%; not actual
funded economic EAD accuracy. Current UPB is scheduled/stated principal; Default
Amount includes accrued interest; Delinquency UPB reflects participation. Do not
replace LGD denominator or change PD event timing silently. Four selected-column
identical duplicate rows removed, no conflicting histories. Next: reconstruct
assumption-based amortization/I/O schedule, validate against clean performing
history, then compare on matched onset cases. No fitted EAD model or independent
validation yet. Additions local and uncommitted; prior Git checkpoint preserved.

## EAD model candidates fitted — October 6, 2026

See docs/model_development/ead_model_research_2026-10-06.md. External final artifact
ead-research-v0.1.2 uses ead-source-audit-v0.2.0. Two schedule conventions and
fixed alpha10 ridge ratio model; train565 three-month/572 twelve-month. Matched
supported fixed/unmodified/pre-maturity population only. Ridge best2019–22,
IO-clock sensitivity best2023onward. No baseline selected, no verified economic
EAD or EL integration. v0.1.0 annuity/log-model diagnostic superseded; v0.1.1
reload-failed partial artifact unusable. v0.1.2 independent annuity and reload
checks pass. Next: schedule convention evidence, excluded-case coverage,
chronological refit backtests, segment/tail and LGD denominator reconciliation.
Local changes remain uncommitted; prior Git checkpoint preserved.

## EAD diagnostics completed — October 6, 2026

See docs/model_development/ead_diagnostics_2026-10-06.md and external
ead-diagnostics-v0.1.0. Historical expanding refits evaluated754 three-month/
766 twelve-month cases; aggregate error IO-clock0.0967%/0.4727%,ridge0.0971%/
0.3459%. Recent within-IO76 twelve-month cases have unchanged principal; ridge
drifts. Recent43 maturity-crossing cases remain positive exposures; no assumed
balloon payoff. ARM-specific Fannie documentation confirms convention variation,
not fixed-rate clock validation. Recommend transparent schedule candidate and
ridge challenger, no baseline selection. Next: contract-convention evidence,
structural IO guard within explicit funded scope, maturity and excluded-case
coverage, denominator/date integration. Changes local/uncommitted.

## EAD guarded and coverage candidates — October 6, 2026

See docs/model_development/ead_coverage_candidate_2026-10-06.md. Final external
ead-coverage-candidate-v0.1.1; v0.1.0 broader IO route labels superseded.
Explicit IOhold for fixed/unmodified/pre-maturity loans, supported postIO clock
otherwise, flagged hold fallback for maturity/unknown schedules. Coverage1,915/
1,952 initialeligible3/12month cases is proxy coverage, not verified contract.
Recentfull error0.1109%/0.5462% versus hold0.2647%/1.0594%; matched guardedridge
0.0516%/0.2445%. No refit/denominator change/independent validation/baseline
selection. Next: route backtests, participation/accrual/default-date reconciliation.
Local additions remain uncommitted; Git checkpoint remains LGD-to-EAD start.

## Schedule and denominator evidence — October 6, 2026

See docs/model_development/ead_schedule_reconciliation_2026-10-06.md and external
ead-schedule-reconciliation-v0.1.0. One performing window per304 loans: postIO
clock lower error on all64 convention-different loans; partialIO79 error0.1928%
versus calendar0.5776%. Provisional support, not contract validation.672 signed
source identities verified; atfirstSDQ660 scheduled/633 participation positive.
DefaultAmount equals participation withincent418, but negative residual187;
scheduled negative residual158. Do not infer accrual by subtraction or floor.
Median SDQ/disposition gap1.7495years; contractual default date unresolved.
SourceLGD*principal rescales loss identity; maximumcase departure66.48%.
Principal-only research method retained, no automatic EL integration. Next:
date-aligned participation outcome and denominator exception investigation,
separate broader exposure approximation only if supported. Local uncommitted.

## EAD participation/exception review — October 6, 2026

See docs/model_development/ead_participation_review_2026-10-06.md; final external
ead-participation-review-v0.1.2. Same-month participation scoring recent3months
0.1601%(418),12months0.5892%(454), changed target not principal improvement.
Ten source-denominator scale departures>10%; five repeated observedSDQ spells,
three smaller departure with lastspell principal. Hindsight diagnostic, nottrue
default identification. No missing-history/maturitychange/balanceincrease inthese
pre-disposition histories. No case removal or accrual inference. v0.1.0 initial
and v0.1.1 unrestrictedhistory retained diagnostic; v0.1.2 current. Next: explicit
observed episode table, preserve onset/resolution dates and participation basis;
do not select nearest balance as true default or integrate EL silently. Local
uncommitted work; principalmethod and LGD checkpoint unchanged.

## Observed episode table executed — October 6, 2026

See docs/model_development/ead_observed_episodes_2026-10-06.md. External
immutable ead-observed-episodes-v0.1.0:2,416 spells/2,120 loans,238 multiple
spell loans,660 frozenLGD overlap/66 multiple observed spells. Exact raw
participation joined;750 loans with source resolution metadata. Gap boundary
flags and return-to-nonSDQ explicitly notcure. Lastpre-resolution link is
hindsight diagnostic, not true default selection or prospective predictor.
Tests113passed/five skips,lintpasses. Next: first/last spell exposure comparison
on66 linked multiple-spellLGD loans and explicit commonPD/EAD default proposal;
no automatic denominator or EL change. Local uncommitted additions.

## Common timing proposal documented — October 6, 2026

See docs/model_development/ead_pd_timing_proposal_2026-10-06.md; external
ead-episode-alignment-v0.1.0. Repeated66 LGD cases:last principal closer49/farther12;
paired participation63 lastcloser48 and matches source withincent32. Hindsight
sensitivity, not true default or accrual. FirstSDQ repartition oforiginal672:
634through2018/23in2019–22/3in2023+/12unmatched;8oforiginal11OOT originatedbefore2023.
No old metrics relabeled/refit. Proposed common first-observedSDQ PD/EAD event
contract, leftcensor/gaps and payoffexits explicit, repeatedspells separate;
loss finalization/availability and episode LGD attribution unresolved. Next:
SEPARATE versioned firstSDQ PD research experiment/event contract across all2120
onsets; preserve dispositionPD and originalLGD. AutomaticEL disabled. Proposal
not adopted/institutionallyapproved. All EAD additions local/uncommitted.
