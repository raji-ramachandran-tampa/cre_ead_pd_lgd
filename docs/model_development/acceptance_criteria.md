---
title: "CRE Expected Loss Development Acceptance Criteria"
status: "Controlled working draft"
version: "0.1 proposed"
as_of_date: "2026-08-31"
---

# 1. Use of this checklist

These are minimum proposed gates for entry into development, component
selection, integrated implementation, and submission to independent
validation. A result is `Pass`, `Fail`, `Open`, or `Not applicable with
rationale`. Numeric performance thresholds are not invented here; they require
approval before final holdout evaluation. A waived or failed item needs an
identified owner, risk assessment, interim control, due date, and authorized
disposition.

# 2. Development entry gates

| ID | Acceptance criterion | Required evidence | Status |
|---|---|---|---|
| DEV-ENT-001 | Intended and prohibited uses, population, grain, horizon, and users are approved | Signed decision or governance record | Open |
| DEV-ENT-002 | Default, cure, LGD cash-flow, EAD, exit, and censoring definitions are executable | Outcome specification and sample walkthrough | Open |
| DEV-ENT-003 | Data rights, sources, lineage, vintages, and retention are documented | Source inventory and lineage map | Open |
| DEV-ENT-004 | Development, temporal validation, and holdout partitions are fixed | Versioned partition manifest | Open |
| DEV-ENT-005 | Candidate, benchmark, selection metrics, and materiality standards are predeclared | Approved development plan | Open |
| DEV-ENT-006 | Roles, independence expectations, repositories, environments, and change controls are established | RACI and implementation plan | Open |

# 3. Data and outcome gates

| ID | Acceptance criterion | Required test/evidence | Status |
|---|---|---|---|
| DEV-DAT-001 | Declared observation keys are unique | Duplicate-key test | Open |
| DEV-DAT-002 | Source-to-report lineage and snapshot checksums are reproducible | Lineage sample and manifest rerun | Open |
| DEV-DAT-003 | Point-in-time availability prevents future information | Availability-date and leakage tests | Open |
| DEV-DAT-004 | Missingness, exclusions, imputation, and quality flags reconcile by count and exposure | Data-quality report | Open |
| DEV-DAT-005 | Population and outcomes are representative enough for each retained segment | Coverage/bias analysis and uncertainty | Open |
| DEV-OUT-001 | Default flags and dates reproduce approved triggers | Stratified record-level sample test | Open |
| DEV-OUT-002 | Recovery and cost cash flows reconcile to source records | Cash-flow reconciliation | Open |
| DEV-OUT-003 | EAD at default reconciles without LGD double counting | Default-date exposure test | Open |
| DEV-OUT-004 | Unresolved defaults and right censoring are not treated as zero loss/default-free | Censoring diagnostics | Open |

# 4. PD gates

| ID | Acceptance criterion | Required test/evidence | Status |
|---|---|---|---|
| DEV-PD-001 | Risk-set construction handles default, payoff, maturity, and censoring consistently | Person-period reconciliation | Open |
| DEV-PD-002 | Conditional, marginal, survival, and cumulative PD reconcile algebraically | Unit and integration tests | Open |
| DEV-PD-003 | Probabilities remain finite and in `[0,1]`; survival is nonincreasing and cumulative PD nondecreasing | Boundary/property tests | Open |
| DEV-PD-004 | Primary is compared with benchmark and challenger on identical partitions | Candidate comparison table | Open |
| DEV-PD-005 | Calibration, discrimination, stability, uncertainty, and economic sensitivity are acceptable under preapproved standards | Development results | Open |
| DEV-PD-006 | Segment pooling or differentiation is supported by data and performance evidence | Segment analysis | Open |

# 5. LGD gates

| ID | Acceptance criterion | Required test/evidence | Status |
|---|---|---|---|
| DEV-LGD-001 | Raw discounted workout LGD is independently reproducible | Cash-flow recalculation sample | Open |
| DEV-LGD-002 | Discounting convention, costs, guarantees, caps, and post-resolution treatment are approved | Method decision record | Open |
| DEV-LGD-003 | Unresolved-case treatment and resolution selection bias are evaluated | Maturity/censoring analysis | Open |
| DEV-LGD-004 | Primary is compared with collateral and simple empirical benchmarks | Candidate comparison | Open |
| DEV-LGD-005 | Tail, zero-loss, segment, temporal, downturn, and valuation-age behavior are understood | Diagnostic and sensitivity results | Open |
| DEV-LGD-006 | Diagnostic raw LGD reconciles to any production bounds or transformations | Raw-to-output reconciliation | Open |

# 6. EAD gates

| ID | Acceptance criterion | Required test/evidence | Status |
|---|---|---|---|
| DEV-EAD-001 | Contractual balance engine reconciles starting balance, cash flows, draws, and terminal balance | Loan-level golden cases | Open |
| DEV-EAD-002 | Interest-only transitions, amortization, balloon, maturity, prepayment, and modification paths are tested | Boundary and scenario cases | Open |
| DEV-EAD-003 | Future-funding estimates respect approved limits and use supported segments | Limit/bound and support tests | Open |
| DEV-EAD-004 | Projected EAD is finite, nonnegative, and not double counted with LGD | Automated property tests | Open |
| DEV-EAD-005 | Behavioral primary is compared with contractual benchmark out of time | Forecast-error comparison | Open |

# 7. Scenario and aggregation gates

| ID | Acceptance criterion | Required test/evidence | Status |
|---|---|---|---|
| DEV-SCN-001 | Every scenario path has source, units, dates, vintage, geography, transformation, and approval status | Scenario manifest | Open |
| DEV-SCN-002 | Scenario weights are finite, nonnegative, and sum to one within approved tolerance | Automated weight test | Open |
| DEV-SCN-003 | Transmission direction and sensitivity are economically coherent and limitations are disclosed | Sensitivity report | Open |
| DEV-SCN-004 | Scenario and overlay effects are separately identifiable and not duplicated | Double-counting test | Open |
| DEV-EL-001 | Loan-horizon-scenario EL exactly equals marginal PD × LGD × EAD × discount factor | Unit/golden-case tests | Open |
| DEV-EL-002 | Scenario outputs are retained before weighting | Output schema test | Open |
| DEV-EL-003 | Loan results reconcile to all portfolio aggregations by count and amount | Aggregation reconciliation | Open |

# 8. Implementation and evidence gates

| ID | Acceptance criterion | Required test/evidence | Status |
|---|---|---|---|
| DEV-IMP-001 | Reusable authoritative logic is in versioned modules, not notebooks alone | Repository review | Open |
| DEV-IMP-002 | Configuration and paths are portable and contain no credentials or confidential data | Static/configuration tests | Open |
| DEV-IMP-003 | Controlled reruns reproduce results within approved tolerance | Reproducibility test and run manifests | Open |
| DEV-IMP-004 | Independent sample calculations agree with implementation | Implementation-verification report | Open |
| DEV-IMP-005 | Code, data, artifacts, documentation, and tests share traceable versions | Bidirectional crosswalk | Open |
| DEV-EVD-001 | Development report distinguishes results, proposals, limitations, and open decisions | Documentation review | Open |
| DEV-EVD-002 | Assumption, limitation, issue, and change registers are complete and owned | Register review | Open |
| DEV-EVD-003 | Validation receives immutable holdout definitions and a complete reproducibility package | Validation intake record | Open |

# 9. Exit decision

Submission to validation requires all material criteria to pass or receive
documented disposition from the appropriate authority. Submission is not model
approval. Production use additionally requires validation conclusions,
resolved or accepted findings, implementation verification, approval,
monitoring readiness, access controls, and deployment evidence.

