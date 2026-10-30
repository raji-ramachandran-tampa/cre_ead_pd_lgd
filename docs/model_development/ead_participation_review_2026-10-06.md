# EAD same-month participation and large exceptions — October 6, 2026

Lifecycle: development. User authorized review. Status: completed evidence only;
no new fit, baseline/denominator/default-definition change, independent validation
or EL integration. Institutional owner TBD. Amortization remains principal method,
ridge diagnostic only; interest/advances and exact default dates unresolved.

## Date-aligned exposure comparison

Compare frozen primary principal estimates with participation Delinquency UPB in
the SAME first-SDQ reporting month. Participation is an observed exposure proxy,
not established whole-loan principal plus accruals. Scores have a different target
from scheduled/stated UPB. They are sensitivity evidence, not principal-model
improvement. Error = total absolute dollar difference / total participation UPB.

| Horizon | Onset cohort | Positive participation cases | Reference error | Reference aggregate bias |
|---|---|---:|---:|---:|
| 3 months | Through2018 | 957 | 0.1992% | -0.0938% |
| 3 months | 2019–2022 | 495 | 0.3061% | -0.2511% |
| 3 months | 2023 onward | 418 | 0.1601% | -0.0851% |
| 12 months | Through2018 | 977 | 0.7881% | +0.2348% |
| 12 months | 2019–2022 | 480 | 0.8322% | -0.3604% |
| 12 months | 2023 onward | 454 | 0.5892% | +0.2417% |

Earlier3/12month comparisons lack positive participation for45/41 cases; retained
in original population, omitted from this score only. All later eligible cases
have positive participation values. Recent scheduled/participation median ratios
0.99751/0.99771. Same-month scheduled-versus-participation aggregate absolute
difference0.1736%/0.1668%; these differences are NOT identified accrued interest.
Same reporting month is not proof of exact contractual default date. Observed
participation may differ from scheduled balances through payments/basis/allocation;
public fields do not separate causes. Horizons share loans, not independent.

## Large source-denominator exceptions

672 signed LGD cases retained;660 positive scheduled-onset matches. Diagnostic
bands use ABS(scheduled/source DefaultAmount-1): <=1%596,1–5%42,5–10%12,>10%10.
This reciprocal basis differs slightly from prior source/scheduled1% count597;
threshold is descriptive, not policy, exclusion criterion or approval limit.

Ten large cases: eight scheduled principal exceeds source DefaultAmount, two
source exceeds principal. All have positive participation, none participation
matches source withincent, two participation matches scheduled principal.
Source default/event dates stable across recorded histories (no >1 distinct
values); this does not verify their economic correctness or actual default onset.
Loss-sharing types six PariPassu/four StandardDUS, not evidence sharing caused
exposure mismatch. Median firstSDQ-to-disposition gap4.2806years.

Review pre-disposition monthly histories: five cases have multiple observed SDQ
spells and return to non-SDQ, zero observed history gaps, zero maturity-date
changes, zero balance-increase transitions. Three cases have a smaller source
ratio departure using principal at the LAST observed SDQ spell start. This
supports episode/date mismatch as a hypothesis for some loans; it does not prove
cure, redefault, allocation or accrual cause, and does not justify replacing the
first-SDQ definition or frozen LGD denominator. Latest spell is hindsight and
cannot enter prospective features. Do not classify the other cases as explained.

## Recommendation and remaining work

Keep the principal schedule reference and preserve every exception. Build an
explicit observed-delinquency episode table next, with first/last spell, non-SDQ
transitions, maturity and available participation balances. Use it to distinguish
initial exposure forecasting from resolution-linked loss episodes. Never select
the closest balance retrospectively as the true default date. Exact contractual
default/cure and principal-plus-interest breakdown remain unverified. Broader
exposure approximation would need its own declared target/date assumptions.
No automated PD×LGD×EAD until common date, institution/whole-loan perspective and
exposure denominator have been reconciled.

Reproduction: scripts/ead_participation_review.py --artifact-root
<2026Q1-artifact-root> --output <new-directory>. Final immutable external
artifact ead-participation-review-v0.1.2: report.json,participation_comparison.parquet,
large_denominator_exceptions.parquet. v0.1.0 lacks history flags; v0.1.1 all-history
flags superseded by pre-disposition/last-spell checks in v0.1.2. All retained,
not overwritten. Inputs hashed, one-to-one joins enforced, positive-target
comparison coverage recorded. Loan-level details remain outside Git.
History v0.3.0 is unchanged from before accounting-parenthesis parser rebuild;
review uses status/date/principal fields, not that version's signed loss amounts.
Lint and run checks pass. Latest prior suite110passed/five skips; no new core
calculation or full-suite rerun claimed. Local uncommitted additions.
