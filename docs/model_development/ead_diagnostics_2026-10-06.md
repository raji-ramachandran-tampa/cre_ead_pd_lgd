# EAD segment, chronology and maturity review — October 6, 2026

Lifecycle: development. Status: executed diagnostic evidence; no independent
validation, model approval or production use. Institutional owner TBD.
User authorized next diagnostic steps. Source/model definitions remain those in
ead_model_research_2026-10-06.md. Principal-at-first-SDQ proxy only; no change to
LGD denominator or PD default timing. All EAD work remains local/uncommitted.

## Chronological refit results

Four expanding folds: train through2008/evaluate2009–11, through2011/2012–14,
through2014/2015–18, through2018/2019–22. Fixed ridge alpha10 with per-fold
training-only scaling. Unique first-onset loans enforce no loan overlap across
train/evaluation and training outcomes precede evaluation outcomes. Borrower and
MBS dependence are not independently resolved: no grouping purge applied.

All candidates scored on the same complete cases. Error is total absolute dollar
error / total outcome principal. These folds include 2019–22 comparison years;
results are not additional independent evidence. Two horizons share loans.

| Horizon | Evaluated cases | Hold | Calendar-age schedule | Post-IO clock schedule | Ridge |
|---|---:|---:|---:|---:|---:|
| 3 months | 754 | 0.3890% | 0.1406% | 0.0967% | 0.0971% |
| 12 months | 766 | 1.4859% | 0.6459% | 0.4727% | 0.3459% |

Ridge is useful historically at twelve months; recent overall schedule superiority
is not universal superiority of either candidate. No tuning on these results.
The post-IO convention remains a labeled sensitivity, not verified loan terms.

## Recent twelve-month segments

| IO stage, 2023 onward | Cases | Post-IO schedule error | Ridge error |
|---|---:|---:|---:|
| Entire horizon within IO | 76 | 0.0000% | 0.3157% |
| Horizon crosses IO end | 23 | 0.0961% | 0.3124% |
| IO finished at anchor | 60 | 0.4581% | 0.4140% |
| No IO | 91 | 0.2921% | 0.4553% |

Entire-IO scheduled balances were unchanged in these cases; ridge introduces
principal drift that the contractual proxy avoids. Small transition group23 is
exploratory; do not select a segment rule solely from later outcomes. Existing
contractual principle of no principal amortization during IO suggests retaining
schedule treatment for this subset, with explicit no-draw assumption. For actual
funded balances, draw/capitalization/modification possibilities still matter.

Post-IO schedule recent errors by anchor balance: <=5m0.1933%(93),5–20m0.3049%(115),
>20m0.1027%(42); corresponding ridge0.3192%,0.5418%,0.2381%. In the after-IO group,
schedule90th absolute relative error0.3053% versus ridge0.3397%; ridge wins aggregate
MAE slightly, not every tail metric. Large exposures and case mix affect totals.

## Maturity cohort and outstanding balloons

Excluded at/beyond anchor-known maturity: 206 three-month,207 twelve-month cases,
all already initial hold eligible. First observed SDQ can occur after a missed
balloon: contractual due date does not establish a funded-balance payoff.
For recent43 maturity-crossing cases, holding principal produces aggregate error
0.1622% at3months and1.7145% at12months. Zeroing all these positive exposures would
produce100% error against the defined principal target. Keep them as a separate
unpaid-maturity exposure branch; no deterministic payoff, cancellation or
refinance assumption is justified. Hold is diagnostic, not selected as a full
maturity model. A training-era maturity case has absolute relative hold error
876.8% at12months: tiny residual balances can make individual relative errors
large despite modest portfolio-weighted error. No case deletion/capping.

## Contract-source review

[Fannie MFLPD glossary](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf)
defines original amortization months and IO end date, but not enough to identify
every amended payment schedule. The original/current fields in revised snapshot
are not proven to have been available on each historical prediction date.

[Fannie August1,2018 ARM partial-IO announcement](https://capitalmarkets.fanniemae.com/mortgage-backed-securities/multifamily-mbs/multifamily-arm-7-6-and-arm-7-4-partial-interest-only-mbs-amortization-schedule-announcement)
documents product-specific disclosure corrections and a remaining-term convention
subtracting elapsed scheduled debt-service payments. It is specific to ARM7-6/7-4,
not evidence that our fixed-rate population must use the same convention. Thus
better fit of post-IO clock does not verify it across all contracts. Current
conversion guide node13766 search excerpt was located, but full page returned403;
not used as verified contract evidence. No account requirement inferred.

## Recommendation and next work

Retain transparent amortization/IO schedules as the principal EAD candidate,
with fixed ridge as challenger. Do not promote the post-IO sensitivity to a
verified contractual baseline merely because it fits later outcomes. Document
amortization-convention uncertainty and inspect clean performing residuals.
A structural IO hold rule is preferable to unconstrained principal drift for
known fixed fully funded loans during IO, but requires explicit scope/draw rules.
Keep unpaid-maturity exposure separate; retain positive balances while examining
amortization/extension/refinancing and available actual delinquency amounts.
Extend missing-schedule/ARM/modified-loan coverage before a portfolio-wide claim.

Artifacts: external ead-diagnostics-v0.1.0/report.json and
historical_predictions.parquet; input audit/model report SHA256 hashes retained.
Code models/ead_diagnostics.py; reproducible CLI requires source,models,output.
Source ead-source-audit-v0.2.0; models ead-research-v0.1.2. No source artifacts
modified. Synthetic tests enforce train/test chronology, distinct loan cohorts
and no use of evaluation outcomes in fitting. No automatic aggregation.
