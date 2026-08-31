---
title: "CRE Expected Loss Model Development Specification"
status: "Controlled working draft"
version: "0.1 proposed"
as_of_date: "2026-08-31"
lifecycle_stage: "Model development planning"
---

# 1. Purpose and status

This specification converts the overarching CRE Expected Loss Model Governance
and Design Document into requirements for reproducible model development. It
covers probability of default (PD), loss given default (LGD), exposure at
default (EAD), scenarios, discounting, expected-loss aggregation, and supporting
data and controls.

The initial intended use is economic expected-loss measurement and scenario
analysis. CECL, IFRS 9, regulatory capital, formal supervisory stress testing,
and production decisioning are prohibited unless an approved use-specific
policy layer, validation, implementation verification, and authorization are
added. This document records proposed design decisions; it does not establish
model approval or regulatory compliance.

## 1.1 Audience and decisions supported

The audience comprises model developers, model owners, data owners,
implementation teams, independent validation, Model Risk Management, internal
audit, and authorized approvers. The document supports decisions on data
fitness, outcome definitions, candidate methods, model selection,
implementation equivalence, limitations, and readiness to enter validation.

## 1.2 Governing hierarchy

Development must follow applicable law and regulation, authoritative accounting
requirements for any approved accounting use, SR 26-2, enterprise model-risk
policy and standards, the model governance and design document, and approved
project decisions. Institutional policy mappings and accounting applicability
remain `TBD`.

# 2. Scope, population, and observation unit

| Item | Proposed specification | Status |
|---|---|---|
| Population | U.S. CRE loans for which required exposure, property, performance, and outcome data are available | Proposed |
| Property types | Multifamily, office, retail, industrial, hotel, and other explicitly mapped CRE | Proposed |
| Grain | One loan-property-quarter | Proposed |
| Interval | Calendar quarter with explicit as-of and availability dates | Proposed |
| History | Long enough to cover benign and stressed conditions; exact dates depend on data assessment | Open |
| Forecast horizon | Quarterly through contractual life or approved maximum horizon | Open |
| Geography | U.S.; MSA/state/division hierarchy subject to data support | Proposed |
| Currency | U.S. dollars, with units stored explicitly | Proposed |
| Multi-property loans | Allocated using an approved rule or retained at facility level with relationship keys | Open |

Construction, development, revolving, participation, and cross-collateralized
facilities require separately demonstrated data and methodology fitness. They
must not be silently pooled with stabilized term loans.

# 3. Required definitions

## 3.1 Default and risk-set exit

Default is a first occurrence of an approved trigger such as 90-or-more days
past due, nonaccrual, foreclosure, deed in lieu, bankruptcy with credit loss,
or distressed restructuring/modification meeting the approved definition. The
exact trigger hierarchy, source fields, effective dates, and exception rules
are `To Be Approved` before outcome construction.

For first-default PD, a facility exits the risk set at first default, payoff,
maturity, sale, transfer outside observable coverage, or data censoring. Cure
does not erase a prior default. Re-default requires a separately specified
risk-entry rule and cure window.

## 3.2 LGD

Realized LGD is proposed as:

`LGD = 1 - present value(net recoveries after workout costs) / EAD at default`

Cash flows must carry event, accounting, and availability dates. Discount rate,
recovery scope, cost taxonomy, post-resolution cash flows, guarantees, sale
proceeds, negative and above-100-percent observations, and unresolved cases are
open decisions. Unresolved cases must never be coded as zero loss solely due to
missing resolution.

## 3.3 EAD

EAD at each horizon equals projected funded balance plus approved accrued items
and expected future funding, without double counting items captured in LGD.
Term-loan projections must address amortization, interest-only periods,
balloons, maturity, prepayment, and modification. Construction and revolving
facilities additionally require limits, commitments, utilization, draw timing,
and credit-conversion treatment.

# 4. Data and lineage requirements

The detailed proposed contract is in `data_dictionary.md`. Every modeled value
must support this lineage:

`source -> raw field -> standardized field -> transformation -> feature or outcome -> estimate -> aggregation -> report`

Each source snapshot must retain source identity, retrieval timestamp, coverage
period, publication or availability date, license/terms reference, schema
version, transformation version, row counts, quality results, and checksum.
Raw snapshots are immutable. Corrections create new versions and documented
reconciliation, rather than overwriting history.

## 4.1 Point-in-time controls

- A feature may use only information available by its prediction as-of date.
- Economic reference date, publication date, revision vintage, retrieval date,
  execution date, and outcome date must remain distinct.
- Revised public macro series require a documented vintage policy.
- Joins must declare cardinality and fail on unexpected duplication.
- Imputation indicators must accompany material imputed values.
- Post-default and post-resolution information is prohibited from pre-default
  PD features.

## 4.2 Data assessment deliverables

Development must produce a source inventory, profiling report, missingness and
coverage analysis, duplicate and reconciliation report, outcome incidence and
maturity analysis, representativeness assessment, exclusions table, and data
limitations register. Public-data proxies must be labeled and evaluated for
geographic, property-type, lender, balance, and cycle bias.

# 5. Sampling and experimental design

The development sample must be divided by time, not randomly alone. A proposed
scheme is training, temporal validation, and final out-of-time test, with dates
selected after coverage analysis. The final test set is held back from feature
and methodology selection.

All exclusions require a reason code, before/after counts, exposure impact, and
bias assessment. Repeated quarterly observations must remain grouped by loan
when resampling or cross-validating. Class imbalance methods must preserve
calibration or be followed by explicit recalibration.

# 6. Feature engineering specification

Candidate features may include current and stressed LTV, DSCR, debt yield,
occupancy, NOI growth, valuation age, delinquency state, maturity proximity,
interest-rate structure, amortization, property type, geography, vintage,
market rent/vacancy, employment, rates, spreads, and inflation.

Each retained feature requires a feature ID, business definition, formula,
units, direction expectation, source fields, date alignment, missing-value
treatment, winsorization or transformation, allowed use, leakage review,
stability evidence, and implementation test. Transformations learned from data
must be fitted on training data only.

# 7. PD development requirements

A quarterly discrete-time hazard model is the proposed primary architecture.
It estimates conditional hazard for surviving observations. Marginal PD at
horizon `h` equals hazard at `h` multiplied by survival through `h-1`, and
cumulative PD is the sum of marginal PDs through the horizon.

Development must compare a transparent segment/vintage benchmark, the primary
hazard specification, and at least one proportionate challenger. Evaluation
must cover discrimination, calibration, outcome incidence, temporal and segment
stability, horizon consistency, uncertainty, economic sensitivity, competing
exits, censoring, and sensitivity to default and cure definitions.

Required mathematical controls include hazards and probabilities in `[0,1]`,
nonnegative marginal PD, nonincreasing survival, nondecreasing cumulative PD,
and cumulative PD no greater than one within numerical tolerance.

# 8. LGD development requirements

Development must establish a discounted workout cash-flow dataset before model
estimation. A collateral-value haircut benchmark and an empirical workout model
must be compared. A two-part model—probability of positive loss followed by
severity conditional on positive loss—is the proposed primary candidate when
zero-loss observations are material.

Testing must address resolution selection, unresolved censoring, recovery and
cost timing, collateral value age, workout path, property and geography mix,
downturn sensitivity, negative or greater-than-one raw LGD, and uncertainty in
sparse segments. Any bounds applied for production must be distinguished from
uncapped diagnostic outcomes.

# 9. EAD development requirements

The benchmark is deterministic contractual balance projection. The primary
term-loan approach adds empirically supported prepayment, modification, and
maturity behavior. Facilities with future funding require a separately fitted
utilization or conversion-factor component and sufficient observations.

Testing must reconcile starting balance, contractual cash flows, draws,
paydowns, accruals, and terminal balance; cover interest-only transitions and
balloons; and demonstrate finite nonnegative exposure. Contractual logic takes
precedence over statistical complexity where data cannot support estimation.

# 10. Scenarios and expected-loss aggregation

Scenario inputs must specify variable, geography, frequency, units, reference
date, publication vintage, path, source, transformation, weight, approval, and
effective dates. Scenario labels alone are not sufficient specifications.

The authoritative calculation is performed for each loan, horizon, and
scenario:

`EL(i,t,h,s) = marginal_PD(i,t,h,s) * LGD(i,t,h,s) * EAD(i,t,h,s) * DF(h)`

Scenario-specific results are retained before weighting. Scenario weights must
be finite, nonnegative, and sum to one within approved tolerance. Aggregation
must reconcile exactly from loan-horizon results to every reported portfolio
total. Scenario effects and management overlays require a double-counting test.

# 11. Candidate selection and documentation

Candidate details are in `methodology_candidates.md`. Selection criteria and
their relative priority must be fixed before reviewing final holdout results.
Selection considers conceptual fit, data support, out-of-time performance,
calibration, stability, uncertainty, interpretability, operational complexity,
implementation risk, and monitoring feasibility. Complexity requires a
material, stable, and explainable benefit over the benchmark.

Rejected methods must remain documented with evidence and rationale. Developer
judgment, overrides, and manual exclusions require named ownership and review.

# 12. Implementation specification

Reusable logic must reside in typed Python modules; notebooks may create
exploratory and development evidence but are not the sole implementation.
DuckDB is the analytical query engine and Parquet is the typed storage format.
Configuration controls parameters, segments, scenarios, feature versions, and
model versions without hard-coded local paths.

A run manifest must identify source snapshots and checksums, code revision,
environment and dependency versions, configuration, feature/outcome/model
versions, scenario vintage, random seed, run timestamp, row and exposure
reconciliations, and artifact locations. The same controlled inputs must produce
the same authoritative outputs within specified numerical tolerance.

# 13. Required testing

Testing includes unit, schema, data-contract, integration, reconciliation,
boundary, missing-value, duplicate-key, date-alignment, leakage, probability,
monotonicity, scenario-weight, regression, reproducibility, and performance
tests. The minimum gates are enumerated in `acceptance_criteria.md`.

Independent implementation verification must recreate selected calculations
from controlled inputs and confirm scoring, calibration, scenario application,
discounting, aggregation, reporting, and configuration behavior.

# 14. Development evidence package

The development stage must produce:

1. Development report with purpose, data, methods, results, selection, and limitations.
2. Versioned source inventory, data contract, quality and representativeness report.
3. Outcome specification and independently reviewable outcome samples.
4. Feature dictionary and leakage review.
5. Reproducible notebooks and reusable code.
6. Candidate, benchmark, challenger, sensitivity, and stability results.
7. Final fitted artifacts, calibration objects, configuration, and run manifest.
8. Test, reconciliation, and implementation-verification results.
9. Limitations, assumptions, decisions, issues, and change registers.
10. Bidirectional design-to-code-to-test crosswalk.

# 15. Open decisions and approvals required

| Decision | Current status | Required authority |
|---|---|---|
| Enterprise model ID, tier, owner, and developer | TBD | Enterprise governance |
| Approved intended use and prohibited-use wording | To Be Approved | Model owner and MRM |
| Accounting and regulatory applicability | Open | Finance, Legal/Compliance, MRM |
| Population, exclusions, and multi-property treatment | Proposed | Model owner |
| Default, cure, re-default, and exit definitions | To Be Approved | Credit policy, owner, MRM |
| LGD cash flows, costs, discount rate, and censoring | Open | Credit/Finance, owner, MRM |
| Horizon, data window, partitions, and minimum support | Open | Development and validation |
| Final methodology and calibration | Not selected | Development, then validation and approval |
| Scenario variables, paths, and weights | Open | Scenario governance |
| Monitoring thresholds and use restrictions | TBD | Owner, validation, MRM |

# 16. Completion condition

This specification is ready for approval only when material definitions and
scope decisions are resolved, each requirement has an owner and test, data
availability is demonstrated, validation has challenged the design, and
authorized reviewers record disposition. Model development is not complete
until the evidence package exists and all acceptance gates are passed or
formally dispositioned.

