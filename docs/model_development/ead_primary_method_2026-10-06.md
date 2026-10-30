# EAD primary method decision — October 6, 2026

User agreed to contractual amortization as primary and ridge as a diagnostic
challenger. This method decision supersedes earlier no-primary-method statements;
it does not approve a statistical model, validate a reconstructed contract,
select a discounting/exposure policy or authorize production expected loss.
Lifecycle: research development; owner institutional TBD; independent validation
and institutional approval open. Git baseline checkpoint pending.

## Primary implementation and meaning

Known payment schedules should drive deterministic funded principal projections,
using the existing project_contractual_ead interface for explicit principal/draws.
Public-data research reconstructs assumed schedules via ead_amortization.py and
prepare in ead_research.py. Keep the post-original-IO clock as provisional research
reference; calendar-age convention remains alternative. User approval of the
method does not establish correctness of either convention for individual loans.

Configuration: config/ead_research.yaml. Deterministic principal is primary;
guarded ridge is diagnostic only, not required to score the primary schedule.
IOhold means no scheduled principal repayment within known fixed/unmodified
pre-maturity IO period, assuming no funding/capitalization changes. Missing or
modified/ARM schedules use an explicitly flagged balance-hold proxy. Maturity
crossings retain a separately flagged unpaid-balloon balance proxy; do not infer
payoff or refinance. These fallbacks are not contractual schedule reconstruction.
No statistical prediction fills a contract-data gap without separate evidence.

## Frozen research reference

External ead-schedule-reference-v0.1.0 packages only the primary predictions and
explicit basis/verification flags from ead-coverage-candidate-v0.1.1; no refit,
recalibration or new accuracy claim. Includes3,867 horizon-case rows, not unique
independent loans. manifest.json hashes source report/predictions and current
configuration. No ridge predictions/model required in selected table. Exact
rowwise identity with prior coverage predictions verified. Raw/derived loan-level
files remain outside Git. Original candidates preserved for rollback/comparison.

Recent full-eligible principal error remains0.1109% at3months(418 cases) and
0.5462% at12months(454). Target scheduled/stated UPB at first observed SDQ;
not verified actual principal+interest at contractual default. Source DefaultAmount
already includes accrued interest; multiplying it-based LGD by scheduled principal
would change loss basis. PD currently uses proposed disposition-based events,
so no silent EL integration or shared-default claim.

## Work still required

Verify exact payment schedules, original IO/amortization convention and month
alignment against clean performing histories or loan documents. Where explicit
contractual principal cash flows exist, use them instead of regression. Model
actual-versus-scheduled principal, missed balloon/extension and accrual/advances
only as separately defined outcomes with available observed labels. Do not treat
missing funding/accrual information as zero. Reconcile participation and default
amount with onset dates before combining PD/LGD/EAD. Complete future independent
validation; do not present small errors on scheduled values as economic exposure
accuracy. Latest full suite110passed/five skips; this step is designation/packaging,
not a new fit or change to core tested formulas. Local uncommitted changes.
