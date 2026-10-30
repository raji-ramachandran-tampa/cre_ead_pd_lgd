# EAD branch and advanced-model feasibility — October 30, 2026

Lifecycle: development research. User requested an EAD branch and feasibility
assessment given existing data. Branch ead-model-development starts from LGD
checkpoint33b4c00 and preserves earlier EAD work. Existing primary method remains
deterministic amortization; guarded ridge diagnostic challenger. No new advanced
model fitted, no performance claim, independent validation/approval open.
Institutional owner TBD; research population Fannie multifamily, not all CRE.

## Feasibility decision

A more advanced public-data PRINCIPAL/REPORTED EXPOSURE model is feasible as a
controlled experiment. A more complex estimator alone cannot identify unobserved
funding, accruals or exact contractual default. Need measured chronological gains
over amortization and guarded ridge before replacing a method that is already
appropriate for known term-loan principal cash flows. Retain deterministic schedule
and IO rules as the structural backbone, not a regression replacement for arithmetic.

Verified local evidence:2120 first observed SDQ loans;2416 observed spells,238
multi-spell loans, not2416 independent defaults. Scheduled/EAD matched coverage
1915 three-month and1952 twelve-month cases. Earlier ridge supported565/572
training cases, not the full monthly sample. Performing schedule diagnostic304
unique supported loans despite22045 repeated windows. Small independent cohort
counts and narrow targets limit justified complexity and uncertainty assessment.
Existing recent periods already examined; do not label them untouched tests.

## Proposed advanced experiment, not implemented evidence

Stage1: preserve schedule forecast and route-quality flags. Verify contract/IO
convention and availability. Principal forecasts remain held during known IO under
explicit no-draw/capitalization assumptions; unknown/maturity holds stay flagged.

Stage2: fit a shallow nonlinear residual challenger using available dated
rate,age,maturity,IO,prior observed balance behavior and schedule information.
Define the target BEFORE fitting:
- scheduled principal minus schedule forecast, normalized by starting principal,
  tests schedule reconstruction only; or
- reported participation UPB at first SDQ minus schedule forecast, normalized by
  starting principal, tests a SOURCE-SPECIFIC exposure proxy.
These are different targets. Participation residual may reflect date/reporting/
allocation basis, not just missed payments. Never call it identified interest.
No label change to frozen LGD. IO principal rules do not force participation
residual zero when exposure bases differ. The latter target is a separate branch
outcome and must retain explicit institution/whole-loan limitation.

Stage3: compare mean and quantile residual forecasts. Gradient boosting supports
squared-error and quantile losses in official scikit-learn documentation; inspect
installed-version API before implementation, no dependency upgrade implied.
Predicted quantiles are not automatically calibrated intervals or EL means.
Report empirical coverage, quantile crossing and tails on held-out chronological
folds; sparse extremes may preclude reliable intervals. Prefer shallow trees,
restricted parameters and simple benchmarks, no large model search.

Evaluation: loan-disjoint chronological folds, borrower/MBS dependence review,
training-only preprocessing/parameter choice, actual outcome availability cutoffs,
consistent horizons, paired-positive target coverage, dollarMAE/aggregate error,
bias, segment/tail metrics, and case-level stability. Preserve all exceptions.
First-SDQ event alignment with PD is proposed, not implemented. Last spell/source
resolution info is outcome metadata only, never prospective features. Macro features
require separate rationale, date alignment and evidence of incremental benefit.
Do not reuse PD variables merely to make the model appear more advanced.

## What current data cannot establish

CCF/future draw model: no linked undrawn commitments, facility limits or draw
histories in current inspected public extract. Credit facilities excluded from
term-loan benchmark. Additional lender/facility data required.
Full economic EAD: separate accrued interest, servicing/other advances and funding
cash flows are missing. DefaultAmount includes interest but exact timing/basis
and decomposition unverified; cannot infer a universal add-on from subtraction.
Contractual cure/redefault or definitive balloon-payoff mechanism: observed
payment-status transitions are proxies, not loan-document verification.
Integrated economicEL: PD disposition timing, firstSDQ EAD timing and sourceLGD
denominator still differ. Advanced fitting does not reconcile these definitions.
Do not claim that a public-source principal model estimates these missing quantities.

## Recommendation and implementation scope

Proceed on EAD branch with a HYBRID research challenger: deterministic schedule
plus modest nonlinear residual/uncertainty experiment, using declared supported
targets. Keep amortization primary until reproducible paired out-of-time evidence
justifies added complexity. Retain guarded ridge as simpler comparator. No need to
refit existing PD or alter closed LGD just to test this EAD experiment. The common
PD/EAD event-definition branch remains a separate change requiring impact analysis.
This assessment does not assert better results are guaranteed or that advanced
modeling is impossible. Main limitation is observable outcome quality and exposure
basis, not access to a sufficiently complicated algorithm.

Sources reviewed October30:
[Fannie MFLPD glossary](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf)
defines principal,participation,DefaultAmount and loan contract fields; local raw
header/audit determines inspected field availability.
[Scikit-learn HistGradientBoostingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html)
describes mean/quantile losses; capability, not empirical EAD effectiveness.

Change scope: EAD development branch/checkpoint only. Raw/derived loan data and
serialized models remain outside Git. Existing LGD and PD frozen artifacts retained.
Rollback returns to main checkpoint; primary EAD artifact versions preserved.
