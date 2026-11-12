# A Reproducible Public-Data Framework for Multifamily Credit Risk: Default Timing, Signed Loss Severity, and Exposure Projection

**Working draft v0.2 — November 12, 2026.** Authors and affiliations: to be confirmed.
This draft contains evidence-backed initial sections and explicitly identifies
unfinished analyses. It is not a submission-ready manuscript.

## Abstract

Public loan-performance data support reproducible credit-risk research, but
inconsistent default dates and exposure definitions can obstruct the combination
of probability of default, loss given default, and exposure at default. We develop
a research framework using Fannie Mae multifamily loan-performance data, preserving
source-reported signed losses and distinguishing scheduled principal from reported
participation exposure. The signed-loss sample contains 672 resolved outcomes,
including 88 negative reported loss ratios. An exposure analysis identifies 2,120
loans with observed serious delinquency and constructs 2,416 observed delinquency
spells. Contractual amortization provides the primary principal-exposure method;
ridge and nonlinear schedule-residual models provide statistical challengers.
A nonlinear challenger improves twelve-month historical aggregate absolute error
from 0.4727% to 0.2160%, but performs worse than amortization on the examined recent
cohort, at 0.2154% versus 0.1937%. Reconstruction from prior balances yields
small additional improvements but qualifies for few recent cases. First-versus-last delinquency comparisons reveal
material timing differences between initial distress and resolution-linked loss
exposures. These findings demonstrate the importance of outcome reconciliation,
transparent deterministic benchmarks, and chronological evaluation. They do not
establish a complete economic expected-loss model: exact default attribution,
accruals, advances, and undrawn commitments remain unresolved. The implementation
also documents AI-assisted development with versioned code, tests, and evidence;
no causal productivity advantage is estimated.

**Keywords:** multifamily mortgages; credit risk; exposure at default; loss given
default; amortization; reproducibility.

## 1. Introduction

A credit-loss estimate depends on both the size of an exposure and the event to
which the loss is attributed. A loan can first become seriously delinquent,
subsequently return to a less delinquent state, and eventually be liquidated years
later. A balance measured at the first observed delinquency need not equal the
exposure used in a loss ratio reported after resolution. Likewise, a scheduled
principal balance is not necessarily the same quantity as an institution's actual
participation exposure or principal plus accrued interest.

This study examines those distinctions within a public-data multifamily credit-risk
framework. Its initial objective is to develop transparent PD, loss-severity, and
exposure components, while making explicit the evidence needed to combine them.
The empirical population is Fannie Mae multifamily loans; findings should not be
generalized automatically to office, retail, construction, or all commercial real
estate. A second objective is to document an AI-assisted research workflow through
code, tests, immutable external artifacts, and human methodological decisions.
This workflow documentation does not constitute independent model validation.

The intended contribution is an empirical account of how definition and timing
choices affect credit-model research with incomplete public data. We preserve
negative source loss ratios rather than automatically flooring them, use
amortization as a structural principal benchmark, and evaluate additional model
complexity against that benchmark. We report mixed results rather than selecting
the most favorable period or treating a more complex estimator as an improvement
by construction. Establishing this contribution relative to existing work requires
the literature review described below; no priority or first-in-literature claim
is made in this draft.

## 2. Related literature and contribution positioning

**Draft section requiring completion.** The review will separate four strands:
(i) commercial-mortgage default and competing exits; (ii) signed/accounting loss
severity and discounted workout losses; (iii) contractual and behavioral exposure
models; and (iv) reproducible AI-assisted empirical workflows. Evidence from CMBS
servicing data and administrative banking data must not be described as using our
exact public Fannie Mae sample.

Conformalized quantile regression combines quantile estimation with calibration
for predictive uncertainty [R2]. Our temporal calibration experiment evaluates
coverage empirically; temporal dependence and distribution change do not establish
the exchangeability assumptions needed for a coverage guarantee. The related-work
section must explain how this established method is used rather than claim the
method itself as a contribution. See the [source register](references/sources.md)
for the citation audit and research tasks.

## 3. Data and outcome definitions

### 3.1. Source and population

The research uses the Fannie Mae multifamily loan-performance release labeled
2026Q1. The existing monthly table contains 5,392,800 rows across 73,048 loans.
The EAD audit removes four rows identical across selected EAD columns; this is
not a claim that every original raw field is identical. The analysis uses a revised
snapshot, and historical field publication dates are not fully observed. Thus,
chronological splitting alone does not establish point-in-time availability.
Source definitions are taken from the Fannie Mae attribute glossary [R1].

Different components use different populations. The signed-loss sample has 672
resolved cases: 632 training outcomes, 29 development-validation outcomes, and 11
examined later outcomes under the existing disposition-year partitions. Training
includes 547 positive, 72 negative, and 13 zero losses; the later samples contain
another 16 negative outcomes. Exposure research includes unresolved and cured-status
loans rather than restricting the population to loans with resolved losses.
The initial EAD analysis finds 2,120 loans with observed first serious delinquency.
Repeated spells are not independent loans or independently verified defaults.

### 3.2. Default, delinquency, and resolution

Observed serious delinquency is defined as an SDQ indicator of Y or payment status
of 60–89 or 90+ days delinquent. Observed spells are separated by a transition to
non-SDQ status or a gap in reporting. A return to 30–59 days delinquent is not
necessarily a cure. A spell at the start of the observed history may be left
censored. The last spell before disposition is a hindsight diagnostic association,
not proof of the contractual default underlying the realized loss.

Existing PD experiments use a proposed event derived from source credit-event
or disposition timing. A common first-observed-SDQ timing definition for future
PD/EAD work has been proposed but not implemented in those frozen PD models.
**PD quantitative results and their label/date assumptions must be audited and
added before this manuscript can support claims about the full framework.**

### 3.3. Loss severity and exposure basis

The primary loss-severity target is

\[
L_i=\frac{\text{source-reported signed net loss}_i}
           {\text{source Default Amount}_i}.
\]

The glossary describes Default Amount as principal plus accrued interest at
default, current UPB as scheduled or stated principal, and Delinquency UPB as
Fannie's participation balance at delinquency [R1]. Differences between these
fields therefore cannot automatically be interpreted as accrued interest.
Negative source loss ratios are preserved; source-reported net benefits and
accounting adjustments require reconciliation rather than automatic censoring.

A separate assumption-based discounted accounting approximation is

\[
L_i^{\mathrm{proxy}}=1-\frac{1-L_i}{(1+r)^{T_i}}.
\]

Here the net accounting equivalent, timing, and rate are assumptions. This is not
a reconstruction of complete observed recovery and expense cash flows. Changing
this target changes the meaning of its prediction errors; errors across the two
targets are not a direct model-improvement comparison.

## 4. Methods and evaluation

### 4.1. Component framework

A coherent expected-loss calculation would combine marginal default probability,
conditional loss severity, exposure, and discounting at matching loan, horizon,
and scenario definitions. This supplies the design objective, not a completed
empirical result. The current principal forecast, source-loss denominator, and
existing PD event do not yet have a common verified basis. We do not report their
mechanical product as validated economic expected loss.

### 4.2. Loss models

The working signed-loss reference is ridge regression with acquisition LTV,
underwritten DSCR, acquisition-balance size, property and loss-sharing categories,
and six-month CPI change. Training-only preprocessing is used, with ridge penalty
10. CPI is revised and its availability lag is assumed. Negative outcomes remain
in the target. Simpler mean and no-macro models and a signed hurdle model are
retained as comparators; complete manuscript specifications will be reproduced
from their frozen configurations.

### 4.3. Exposure models

Known contractual principal repayments imply a deterministic principal projection.
Public fields require schedule reconstruction, so we retain calendar-age and
post-original-interest-only amortization conventions, with the latter serving as
a provisional research reference. Principal is held constant during a supported
interest-only horizon. Missing schedules and unpaid maturity balances use explicitly
flagged hold estimates; these are proxies, not verified reconstructed contracts.

The nonlinear challenger learns the residual

\[
y_i=\frac{B_{i,\mathrm{SDQ}}-\widehat B_{i,\mathrm{schedule}}}{B_{i,0}},
\qquad
\widehat B_{i,\mathrm{advanced}}=
\widehat B_{i,\mathrm{schedule}}+B_{i,0}\widehat y_i.
\]

The scheduled-principal target is not a credit conversion factor. Six inputs are
the schedule balance fraction, loan age, note rate, remaining IO months, months
to maturity, and log starting balance. Shallow histogram boosting uses fixed
parameters without a search on later outcomes. Statistical principal predictions
retain the structural IO rule. Separate 3- and 12-month models are evaluated on
supported fixed-rate, unmodified, pre-maturity cases. Full contractual details,
CCF-driven draws, interest, and advances are not recovered by fitting this model.

### 4.3.1. Prior-payment reconstruction

A second deterministic challenger infers payments from four consecutive balances
ending at the forecast anchor. For fixed annual decimal rate \(r\), each prior
month implies \(P_t=B_{t-1}(1+r/12)-B_t\). We take the median of the three implied
payments only when their range does not exceed the larger of $1 or 0.1% of the
absolute median. The three-month lookback and stability tolerance were specified
before evaluating this experiment; they were not selected to improve recent scores.

Qualifying histories must be Current and non-SDQ, have unchanged fixed rates and
maturity, no documented modification or prior balance increase, and a forecast
ending before known maturity. Histories crossing an interest-only transition,
missing records, or failing the stability rule retain the existing schedule or
flagged hold estimate. The reconstructed payment drives an annuity recurrence;
negative or exhausted projections are rejected rather than interpreted as balloon
payoff. No future principal outcome is used to infer the payment. The method does
not estimate paid cash receipts, accrued interest, advances, or contractual truth.

### 4.4. Time partitions and metrics

Exposure mean models fit through 2018. Expanding historical folds train through
2008, 2011, 2014, and 2018, evaluating the following periods through 2011, 2014,
2018, and 2022, respectively. Refit evaluation contains 754 three-month and 766
twelve-month cases; periods include later development-validation years and must
not be summed as independent evidence. Loans are disjoint within each temporal
split, while borrower and securitization dependence remain unresolved.

LGD MAE is reported in loss-ratio percentage points. The exposure aggregate error is

\[
\mathrm{AAE}=100\frac{\sum_i |\widehat B_i-B_i|}{\sum_i B_i}.
\]

This differs from mean absolute percentage error and gives larger exposures more
influence. Uncertainty models fit quantiles using outcomes through 2014 and
calibrate on 2015–2018, separately from the mean-model fit. The nominal interval
coverage is 90%; actual later coverage is reported, including non-IO cases.

## 5. Initial results

### 5.1. Signed loss severity

The CPI ridge reference has historical MAE 28.148 percentage points over 615
backtest cases, development-validation MAE 35.640 over 29 cases, and examined
later-period MAE 79.161 over 11 cases. Its historical improvement over no-macro
ridge is small and concentrated in early folds; the later sample remains sparse
and poorly predicted. These results do not establish broad macroeconomic
predictive superiority or a production-quality LGD model.

### 5.2. Principal exposure

Table 1 compares models on identical supported cases. Errors are AAE percentages.

<!-- EAD_ADVANCED_TABLE_START -->
| Horizon and cohort | Cases | Amortization | Guarded ridge | Nonlinear residual |
|---|---:|---:|---:|---:|
| 3-month, historical refits | 754 | 0.0967 | 0.0727 | 0.0776 |
| 12-month, historical refits | 766 | 0.4727 | 0.2661 | 0.2160 |
| 3-month, 2019–2022 | 306 | 0.1198 | 0.0768 | 0.0811 |
| 12-month, 2019–2022 | 305 | 0.5850 | 0.2860 | 0.2170 |
| 3-month, 2023 onward | 226 | 0.0226 | 0.0516 | 0.0619 |
| 12-month, 2023 onward | 250 | 0.1937 | 0.2445 | 0.2154 |
<!-- EAD_ADVANCED_TABLE_END -->

The nonlinear model improves twelve-month historical aggregate errors but does
not outperform amortization in the examined recent cohort. Amortization therefore
remains the primary research method. Recent nominal 90% intervals cover 85.63%
of non-IO three-month cases and 89.08% of non-IO twelve-month cases. Overall coverage
is higher because deterministic IO cases are included; this must not obscure
undercoverage in amortizing loans.

### 5.3. Prior-payment reconstruction and residual drift

The recent cohort needs smaller aggregate corrections to the amortization
forecast than the nonlinear model supplies. At twelve months, the required net
correction is 0.06801% of total observed principal, while the model adds 0.28106%.
In the 2019–2022 cohort, the corresponding corrections are 0.58466% and 0.55580%.
This is descriptive evidence of oversized recent corrections, not a causal
explanation or a reason to recalibrate on already examined outcomes.

Table 2 compares the prior-payment challenger with the existing routed reference
on the full initially eligible population. These cases differ from the supported
model population in Table 1. Both forecasts retain estimates for histories that
do not qualify for reconstruction; the new method does not drop difficult cases.

<!-- EAD_PAYMENT_TABLE_START -->
| Horizon and cohort | Cases | Routed amortization reference | Prior-payment challenger |
|---|---:|---:|---:|
| 3-month, through 2018 | 1002 | 0.16674 | 0.15166 |
| 12-month, through 2018 | 1018 | 0.74329 | 0.69669 |
| 3-month, 2019–2022 | 495 | 0.15369 | 0.14851 |
| 12-month, 2019–2022 | 480 | 0.66909 | 0.66209 |
| 3-month, 2023 onward | 418 | 0.11093 | 0.10836 |
| 12-month, 2023 onward | 454 | 0.54619 | 0.54087 |
<!-- EAD_PAYMENT_TABLE_END -->

The strict reconstruction rule qualifies for 111 of 1,915 three-month and 115 of
1,952 twelve-month horizon cases. Only six of 418 recent three-month cases and
four of 454 recent twelve-month cases qualify. Thus the recent error reductions
are modest, approximately 2.3% and 1.0% relative to the routed reference, and do
not establish broad schedule reconstruction. The stability gate was not relaxed
after inspecting these results. Amortization remains primary and this method is
a limited-coverage challenger.

### 5.4. Timing and denominator alignment

The episode table contains 2,416 observed spells over 2,120 loans, with 238 loans
having multiple spells. Among the 672 signed-loss cases, 660 have pre-resolution
SDQ records and 66 have multiple spells. Last-spell scheduled principal is closer
to source Default Amount than first-spell principal in 49 of 66 cases; it is farther
in 12 and unchanged in five. Among 63 paired positive participation cases,
last-spell participation equals Default Amount within one cent in 32 cases,
compared with ten at first spell. Closeness cannot identify true default ex post.

Eight of the eleven outcomes assigned to the original recent LGD cohort by
disposition year began serious delinquency before 2023. A first-SDQ repartition
would therefore leave only three of these resolved labels in the 2023-onward
cohort. This is a timing sensitivity, not a relabeling of historical results or
proof of genuinely point-in-time model evaluation.

## 6. Discussion, limitations, and reproducibility

The results favor a component-specific interpretation of model complexity.
For known contractual term-loan balances, amortization supplies the structure;
statistical fitting should demonstrate incremental value in deviations, incomplete
schedule reconstruction, or uncertainty. Better historical residual fit does not
imply better recent performance. Prior-payment reconstruction can help when stable
historical balance behavior identifies a payment, but most eligible histories fail
the prespecified stability or contract checks. Small errors against scheduled principal do
not demonstrate accurate economic EAD.

Source exposure definitions and event timing are central limitations. We do not
observe separate commitment limits and draw histories for CCF estimation, complete
interest/advance ledgers, exact contractual default and cure dates, or definitive
episode attribution of lifetime losses. Repeated spells and loan observations do
not create independent sample size. The population is multifamily, later periods
have been examined during development, loss samples are small, and historical
publication availability is incompletely observed. Frozen PD results still require
manuscript-level verification, and the economic-EL aggregation remains unresolved.

Code and aggregate development records are versioned in the
[research repository](https://github.com/raji-ramachandran-tampa/cre_ead_pd_lgd/tree/ead-model-development).
The EAD modeling checkpoint is `fcbf2b5`; the accompanying publication export script
rebuilds Tables 1 and 2 from two frozen aggregate reports and records their SHA256
hashes. This verifies transcription, not independent model reproduction. The
latest model test run recorded 124 passing tests and five skipped document checks;
that result is implementation evidence rather than statistical validation.
Raw data, loan identifiers, derived loan-level tables, and serialized models are
not embedded in this manuscript. Public access must not be equated with an
unrestricted redistribution license. The final data/code statement will identify
actual source access conditions, code revision, dependency versions, artifact
hashes, and reproducible extraction procedures.

AI tools assisted research, coding, testing, and drafting. The final disclosure
must describe the tools and human verification actually performed. Code tests and
traceability are implementation evidence, not independent statistical validation.
We have not measured a causal effect of AI assistance on research speed, quality,
or cost, and make no such claim.

## 7. Draft conclusion

The current evidence supports a transparent public-data research workflow in which
loss signs, exposure bases, and event dates remain explicit. Deterministic principal
projection remains a strong benchmark, while more complex residual models show
period-dependent benefits. A prior-payment method offers modest, limited-coverage
improvements without replacing the primary schedule. A complete economic expected-loss estimate requires
further denominator and event reconciliation. Completing the PD evidence audit,
related-work positioning, and robustness analyses is necessary before submission.

## References

[R1] Fannie Mae. *Multifamily Loan Performance Data Attribute Glossary and File
Layout*, March 2023. [Source](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf).

[R2] Romano, Y., Patterson, E., and Candes, E. *Conformalized Quantile Regression*,
2019. [Author preprint](https://arxiv.org/abs/1905.03222). Bibliographic venue details
and final bibliography to be verified before submission.
