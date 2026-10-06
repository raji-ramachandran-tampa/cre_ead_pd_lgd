# CRE restart — October 6, 2026: LGD checkpoint and EAD start

Status: current research handoff. Audience: developer, user and future reviewer.
Owner: institutional owner TBD. User authorized GitHub checkpoint and transition
to EAD. No independent validation, institutional approval or production release.
Read AGENTS.md, CRE_PROJECT_META_PROMPT.md and tasks/model_development.md.
This supersedes the October 5 restart for current state; retain that document
and linked reports as historical evidence.

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
