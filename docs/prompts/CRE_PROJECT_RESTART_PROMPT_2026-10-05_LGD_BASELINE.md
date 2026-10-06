# CRE Project Restart � October 5, 2026 LGD Research Baseline

Status: current Phase 1 classical research handoff. Read this after AGENTS.md,
CRE_PROJECT_META_PROMPT.md and the matching lifecycle task template. This
supersedes the October 1 handoff for current state, not historical evidence.

## Current baseline decision — October 5, 2026

The user designated the full-population **ridge + CPI** model as the new working research baseline. This decision supersedes earlier "no candidate selected" statements for the working research reference only; no institutional selection, independent validation or production approval is implied. Original no-macro ridge and hurdle artifacts remain preserved comparators.

Current immutable external artifact: `lgd-cpi-baseline-v0.1.0`. It packages model key `0_ridge_cpi` from `lgd-macro-research-v0.1.0`, a selection manifest, source report and selected predictions. No refitting or validation/OOT calibration occurred. Train: 632 through-2018 outcomes. Features: acquisition LTV, underwritten DSCR, log acquisition UPB, property type, loss-sharing type and CPI six-month log change. Ridge alpha remains 10 with training-only preprocessing. Target remains the full signed source net-loss ratio.

MAE percentage points: historical 28.148 (615), validation 35.640 (29), examined OOT 79.161 (11). Historical gain versus original ridge is 0.492 points and concentrated in the early fold; later gain is negligible. CPI uses revised data and an assumed two-month publication lag, so point-in-time performance is unverified. Do not claim discounted economic LGD or automatically feed signed estimates into bounded EL aggregation.

Verification: saved selected model reproduces all 40 later predictions within absolute tolerance 1e-12. Prior full suite: 85 passed, five skipped. This designation changes the reference for subsequent experiments; historical reports retain their original comparison definitions. Current additions remain uncommitted; Git checkpoint/tag is pending. Use original artifacts to revert the working reference if needed.

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

## Subsequent macro experiment — October 5, 2026

See docs/model_development/lgd_macro_research_2026-10-05.md and external lgd-macro-research-v0.1.0. CPI six-month log change improves full-population historical ridge MAE from 28.640 to 28.148 percentage points; later improvement is negligible. National CRE YoY price-change proxy gives small lag-sensitive gains on a shorter matched sample. Revised macro snapshots and assumed publication delays make this exploratory, not point-in-time validation. No unemployment fitted, no candidate selected, frozen baseline unchanged. Full suite: 78 passed, five Pandoc checks skipped.


## Subsequent loan-history experiment — October 5, 2026

See docs/model_development/lgd_history_research_2026-10-05.md. Current external version lgd-history-research-v0.1.1 supersedes retained diagnostic v0.1.0 continuous-rate-change instability. Full 672-loan pre-disposition update and 659-loan before-first-observed-SDQ proxy are separate populations/uses. Lifecycle ridge historical MAE improves 28.640 to 27.920 but validation/OOT worsen; no consistently better overall candidate. DSCR effects depend on assumed reporting lag: two-year primary, one-year sensitivity; actual annual publication dates remain unknown. No default-definition change or model selection. Baseline predictions reconcile and saved hurdle reload reproduces predictions. Tests: 82 passed, five Pandoc checks skipped; new code lint passes.

## DSCR availability evidence audit — October 5, 2026

See docs/model_development/lgd_dscr_availability_2026-10-05.md and external lgd-dscr-availability-audit-v0.1.0. Raw annual file has only loan/year/DSCR; no row publication dates. Fannie announced public file introduction for late January 2021. Only local raw release 2026Q1 exists. Most history-experiment anchors predate 2021; both annual reference-year lags remain retrospective assumptions, not verified point-in-time availability. Distinguish public disclosure from lender statement receipt. This limitation also applies to PD annual-DSCR candidates. Do not infer availability from fiscal year or select lag from accuracy; obtain dated source releases/receipt records.

Archive follow-up: Data Dynamics requires user sign-in; no additional releases retrieved as of this search. Official FAQ Q17 gives Q1 publication by July 14, so monthly Reporting Period Date also does not establish public availability. Archive existence/download options remain unverified behind authentication; do not claim none exist.


Authenticated follow-up: user signed in; MF downloads inspected and current DSCR downloaded. ZIP and CSV hashes exactly match existing 2026Q1 raw source (316,304 rows). No older MF vintage selector or archive was found in the inspected download/message views. Availability gap remains; no model refit or source overwrite.


## Rate and spread macro challengers — October 5, 2026

See docs/model_development/lgd_rates_research_2026-10-05.md and external lgd-rates-research-v0.1.0. Added monthly 10-year Treasury level, six-month yield change and corporate Baa/Treasury spread; two-month assumed lag and three-month sensitivity, separate matched CRE-covered scopes. Full historical ridge CPI MAE 28.148 percentage points versus 31.524 for CPI+Treasury/spread. Spread alone 28.537; validation/OOT improvements are small-sample, already-examined comparisons. CRE-covered combined hurdle gains are modest historically but OOT worsens. No candidate selected; frozen baseline unchanged. Revised snapshots and unverified public release timing remain limitations. Baseline/CPI predictions reconcile within 1e-8; saved combined models reload correctly. Tests: 85 passed, five skipped, one existing pandas warning; new code lint passes. New macro/history/rates research changes remain uncommitted.

## Discounted economic LGD feasibility — October 5, 2026

See docs/model_development/lgd_economic_feasibility_2026-10-05.md and external lgd-economic-feasibility-v0.1.0. Actual 62-field raw schema audited; complete dated recovery/cost/income/reimbursement ledger absent from inspected file. Reported net loss mixes accounting components and is not simply discounted. Credit Event Date is not default onset. Twelve synthetic timing/rate calculations executed using existing calculator; 100 EAD/80 recovery at 5% gives 20% immediate versus 27.44% at two years. No empirical economic target or refit. Next: PD-aligned default/EAD mapping, actual cash-flow contract/accounting reconciliation and explicit rate convention. Current CPI baseline remains unchanged.

## Economic ledger contract implementation — October 5, 2026

See docs/model_development/lgd_economic_contract_2026-10-05.md and models/economic_lgd_contract.py. Dated ledger validation and nominal/discounted reconciliation implemented; no assumed receipts or incomplete ledgers admitted. Explicit institution/whole-loan perspective, rate basis, ACT/365.25, annual effective compounding; signed raw results preserved. Completeness/finalization are caller attestations. Tests 93 passed, five skipped; existing pandas warning. No empirical economic labels possible without missing cash records, no CPI baseline change or EL integration. Local additions uncommitted.

## Public workout source discovery — October 5, 2026

See docs/model_development/lgd_public_workout_sources_2026-10-05.md. Public SEC CMBS trustee exhibit inspected: populated historical loan-level proceeds/expense/net-proceeds table and dated distributions; strongest CRE pilot lead, not proof of complete transaction cash ledger or eligible default sample. Freddie MSIA complimentary monthly investor reports require login; MLPD is partial quarterly outcomes, not full ledger. Single-family datasets have richer components but different population and incomplete payment dates. FDIC paper uses administrative data; no public microdata download found in this search. Recommend separate resolved-multifamily CMBS report-chain coverage pilot; do not pool or match to Fannie without verified crosswalk. No economic model refit or baseline change.

## CMBS initial pilot — October 5, 2026

See docs/model_development/lgd_cmbs_pilot_2026-10-05.md and separate external cmbs-workout-pilot-v0.1.0. One resolved MF foreclosure candidate identified; zero complete economic ledgers. Two nominal identities reconcile exactly; beginning-balance versus loss residual five cents remains unresolved. Combined deductions include P&I advances/unpaid fees; post-liquidation adjustment not proven cash receipt. Raw download HTTP403, no raw report saved; primary web full page and indexed excerpts distinguished. Monthly chain, default/EAD origin, cash dates, decomposition and finalization remain gaps. No empirical economic labels/refit or CPI/Fannie changes. Keep case IDs/amounts outside Git.

## CMBS economic-loss literature — October 5, 2026

See docs/model_development/lgd_economic_literature_2026-10-05.md. Wong 2018 and D Lima/Lopez 2021 use commercial CMBS datasets and nominal liquidation loss ratios; not verified complete discounted ledgers from our SEC/Fannie files. Fees/servicing incentives and advances materially affect loss allocation. Academy 2023 shows NRA recoveries can increase principal paydowns despite expense categorization. FDIC 2015 (different administrative data) explicitly estimates terminal principal recoveries and discounts with assumed timing when full cash histories missing; supports a labeled proxy sensitivity branch, not observed economic labels. No universal rate/cost exclusion or baseline change justified.

## Authorized discounted approximation — October 5, 2026

See docs/model_development/lgd_discounted_proxy_2026-10-05.md, models/lgd_discounted_proxy.py and separate external cmbs-discounted-proxy-v0.1.0. Executed 54 single-case origin/rate/deduction-allocation/timing sensitivities. Not observed economic labels: liquidation balance denominator, distribution receipt date and origin are proxies, combined deductions unseparated. Subsequent adjustment not assumed cash. No chosen rate or confidence bounds, no Fannie refit. Tests 95 passed, five skipped; lint passes. Current CPI baseline unchanged; additions uncommitted.

## CMBS proxy pilot expansion — October 5, 2026

See docs/model_development/lgd_cmbs_expansion_2026-10-05.md and external cmbs-discounted-proxy-v0.2.0. Two resolved MF-classified cases, 108 sensitivities; zero complete observed ledgers. Additional case has documented payment-default and bankruptcy, mixed residential/retail collateral flag. Common transfer-origin/terminal-full-deductions comparison: 5% rate increment varies 1.313–14.143 percentage points versus zero rate. Two cases insufficient to fit or claim stability. Alternative legal origins are different milestones and not poolable. Both post-liquidation adjustments remain unverified cash; first five-cent residual retained, second reconciles. CPI/Fannie unchanged, no population pooling. Prior calculator tests 95 passed/five skipped; new arithmetic checked. Local additions uncommitted.

## Fannie accounting-based discounted approximation — October 5, 2026

User chose Fannie approximation. See docs/model_development/lgd_fannie_accounting_bridge_2026-10-05.md and external lgd-fannie-accounting-bridge-v0.1.0. 660/672 supported first-SDQ-to-disposition durations (620 train/29 valid/11 OOT), 12 missing training durations not imputed; six sensitivities each. Formula 1-(1-L)/(1+r)^(T*f), accounting net recovery equivalent, not observed receipts or verified EAD. Costs/interest/benefits embedded; no extra deductions. Above-one negative net equivalents preserved and positive rate can lower their proxy. 5% terminal mean shifts +5.560/+13.111/+4.873 pp on matched train/valid/OOT; not prediction performance. Tests 98 passed, five skipped. No economic model fitted, no preferred rate, baseline CPI unchanged. Next fit must be matched population and distinguish changed target from predictive improvement; no realized duration feature leakage. Local additions uncommitted.

## Fitted Fannie approximation model — October 5, 2026

User authorized fit. See docs/model_development/lgd_fannie_proxy_model_2026-10-05.md, models/lgd_proxy_model.py and external lgd-fannie-proxy-model-v0.1.0. Primary 5% terminal assumption stated before fit; six sensitivity targets. Final ridge+CPI trained620, historical606, validation29, OOT11. Primary MAE25.611/28.833/75.832 pp; no-CPI26.213/28.866/75.861; mean benchmark better OOT74.003. Same-proxy source-trained CPI comparator26.619/28.081/76.365: proxy refit not consistently better. OOT mean prediction41.733% vs actual proxy0.547%. No realized duration predictor, original pre-disposition features possibly during workout. Different targets: do not choose rate on errors or claim improvement over original target. Saved reload40 predictions verified; tests99 passed/five skipped; lint passes. Original CPI baseline unchanged; no observed economic-LGD/EL claim. Local changes uncommitted.
