# CRE Project Restart — October 5, 2026 LGD Research Baseline

Status: current Phase 1 classical research handoff. Read this after AGENTS.md,
CRE_PROJECT_META_PROMPT.md and the matching lifecycle task template. This
supersedes the October 1 handoff for current state, not historical evidence.

## Objective and decision rights

Continue a governed public-data CRE expected-loss research framework and article.
Empirical population is Fannie Mae multifamily, not all CRE. Classical methods
are current scope; Bayesian/ML are future research. No institutional selection,
validation completion or production/accounting/capital approval exists.

The user explicitly chose the full signed source net-loss ratio, preserving
gains. Economic workout LGD remains a separate outcome. No automatic floor,
cap, case removal, OOT calibration or change of default definition is approved.

## Repository and inputs

GitHub: https://github.com/raji-ramachandran-tampa/cre_ead_pd_lgd . The original
working checkout is the one with the local virtual environment. Resolve data
paths from FANNIE_MFLPD_ROOT and the established path interface; do not assume
an audit clone contains external artifacts. Raw Fannie release is 2026Q1;
processed monthly version v0.3.0; macro snapshot September 16, 2026.

The v0.3.0 monthly dataset has 5,392,800 rows, 73,048 loans and 765 proposed
source credit-event loans. Earlier parsing converted accounting-parenthesis
negative amounts to null. The ingestion parser is corrected for future builds,
but v0.3.0 was not rebuilt. Do not silently overwrite or treat it as corrected.

## Current fitted evidence

PD baseline/revised-macro/vintage candidates and their comparison are unchanged.
No PD primary is selected. See the October 1 handoff for detailed PD metrics;
verify current artifact reports before reuse.

Signed-source-ratio-v0.1.0 has 672 unique loans: training 632 (547 positive,
72 negative, 13 zero), validation 29 (18 positive, 11 negative), OOT 11
(six positive, five negative). Train ends 2018, validation ends 2022; OOT
is 2023 onward and already examined. The eleven eligible OOT cases are all
2023 events. Old 584 nonnegative cases remain unchanged; 88 gains restored.
Signed raw histories reconcile; 93 source-event cases remain excluded.

| Candidate | Historical MAE | Validation MAE | OOT MAE |
|---|---:|---:|---:|
| Signed mean | 30.06 | 37.63 | 76.75 |
| Ridge with loss-sharing | 28.64 | 35.67 | 79.21 |
| Signed hurdle | 29.52 | 37.31 | 76.73 |

MAE units are loss-ratio percentage points. Historical backtests cover 615
cases across four expanding chronological folds with known MBS overlap purged.
MBS transaction IDs are not borrower IDs. Conditional bootstraps exclude
estimation uncertainty. No candidate selected; tiny OOT differences are not
independent confirmation. Hurdle assigns too much positive sign probability
later and understates OOT gain magnitude.

Authoritative fitted versions under external artifacts/2026Q1:
lgd-signed-research-v0.1.0 and lgd-signed-hurdle-v0.1.1. Hurdle v0.1.0 is
superseded due to nonportable entry-point dataclass serialization. Reload
v0.1.1 via SignedHurdle(**joblib.load(path)); do not silently overwrite v0.1.0.

Other external versions: lgd-reconciliation-v0.1.0, lgd-research-v0.1.0,
lgd-research-diagnostics-v0.1.0, lgd-driver-audit-v0.1.0,
lgd-signed-feasibility-v0.1.0, lgd-gain-allocation-audit-v0.1.0,
lgd-outcome-security-review-v0.1.0. Verify manifests/counts/checksums.

## Outcome and collateral findings

Three OOT matured/fully-paid source events have prior serious delinquency.
They remain included; terminal status alone does not justify exclusion. Their
unusual gains dominate the OOT signed mean. All eleven OOT cases show prior
observed SDQ; SDQ is not an approved default-onset definition. The unusual
Full Lender Loss category is absent from training; allocation remains open.

Collateral currently enters statistical models through LTV/property/size
features. New models/collateral.py supplies a deterministic synthetic waterfall:
claim priorities, equal-rank allocation, shared-property global claim limits,
selling costs, timing, external benefits and a separate generic nominal sharing
interface. This is not a Fannie contract mapping or fitted real-data waterfall.
Real run requires complete property/security linkage, competing balances,
current values, dated recoveries/expenses and supported contractual benefits.
Existing EL aggregation requires projected LGD in [0,1], so signed/raw outputs
are not automatically integrated. No approved bounds/discount convention exist.

## Reproduction and baseline checks

Activate the existing Python environment and install project development/modeling
extras if necessary. Run `cre-el test` or `python -m pytest tests -q`.
The October 5 modeling suite returned 75 passed, five Pandoc publication checks
skipped; verify the final baseline result rather than assuming this count.
No Pandoc is installed. Code, synthetic tests and aggregate docs belong in Git;
loan-level outputs and restricted case details stay external.

Baseline scripts accept explicit paths. Dependency order for the existing
external artifacts: initial reconciliation -> driver audit -> signed feasibility
-> signed research -> signed hurdle -> allocation audit -> outcome/security review.
All output versions are immutable; an existing directory requires a new version,
not deletion or overwrite. The baseline uses existing artifacts; fresh-source
rebuild/version choice and source restrictions require their own controlled task.

## Next work

1. Review source allocation and finalization evidence for extraordinary gains.
2. Define default-onset/cure/episode mapping jointly with PD, before any narrower
   default-conditioned LGD target; retain current sample pending that decision.
3. Collect a controlled collateral input package or keep the waterfall synthetic.
4. Compare any new driver/calibration increment on earlier chronological data;
   reserve new future data for independent confirmation.
5. Reconcile signed source outcomes to economic net recoveries before EL use.

Do not infer approvals from baseline commit/tag. Preserve unrelated changes,
inspect git status, test before modifications, and report evidence and open decisions.
