---
title: "CRE Expected Loss Proposed Data Dictionary"
status: "Controlled working draft"
version: "0.1 proposed"
as_of_date: "2026-08-31"
---

# 1. Contract conventions

The proposed analytical grain is one `loan_id`–`property_id`–`as_of_date`
record per quarter. Multi-property allocation remains an open design decision.
Names use `snake_case`; dates use ISO 8601; currencies and percentages carry
explicit units; identifiers are stable pseudonymous keys. `availability_date`
controls point-in-time eligibility.

Required does not mean presently available. Availability, source mapping,
permitted use, and quality must be demonstrated during data assessment.

# 2. Keys and lineage

| Field | Type | Unit/domain | Requirement | Definition and control |
|---|---|---|---|---|
| loan_id | string | Stable key | Required | Pseudonymous facility/loan identifier |
| property_id | string | Stable key | Required | Pseudonymous collateral-property identifier |
| borrower_id | string | Stable key | Conditional | Pseudonymous obligor identifier where permitted |
| as_of_date | date | Quarter end | Required | Observation and prediction date |
| source_id | string | Controlled list | Required | Source system or public dataset |
| source_record_id | string | Source key | Required | Traceable raw-record identifier |
| availability_date | date | Date | Required | Earliest date information could be used |
| snapshot_id | string | Version key | Required | Immutable source snapshot identifier |
| schema_version | string | Semantic version | Required | Applied data-contract version |
| quality_flags | array[string] | Controlled codes | Required | Non-destructive quality and exception indicators |

# 3. Loan and contractual fields

| Field | Type | Unit/domain | Requirement | Definition and control |
|---|---|---|---|---|
| origination_date | date | Date | Required | Contract origination date |
| maturity_date | date | Date | Required | Current contractual maturity |
| original_balance | decimal | USD | Required | Funded principal at origination |
| current_balance | decimal | USD | Required | Principal outstanding at as-of date; nonnegative |
| commitment_amount | decimal | USD | Conditional | Total committed amount for future-funding facilities |
| unfunded_amount | decimal | USD | Conditional | Undrawn commitment; reconcile to limit and funded amount |
| interest_rate | decimal | Fraction/year | Required | Current contractual coupon with basis identified |
| rate_type | category | fixed/floating/other | Required | Interest-rate structure |
| index_name | category | Controlled list | Conditional | Floating-rate index |
| spread_bps | decimal | Basis points | Conditional | Contract spread over index |
| amortization_type | category | amortizing/IO/balloon/other | Required | Contractual principal structure |
| payment_frequency | category | Controlled list | Required | Contractual payment interval |
| recourse_type | category | full/partial/nonrecourse/unknown | Conditional | Borrower recourse status |
| lien_position | integer | Positive integer | Conditional | Collateral lien priority |
| modification_flag | boolean | true/false | Required | Contract terms changed by as-of date |

# 4. Property and operating fields

| Field | Type | Unit/domain | Requirement | Definition and control |
|---|---|---|---|---|
| property_type | category | Approved taxonomy | Required | Primary collateral property type |
| msa_code | string | Census/approved code | Required | Geographic market at as-of date |
| state_code | string | USPS | Required | Property state |
| occupancy_rate | decimal | `[0,1]` | Conditional | Occupied share with measurement date |
| noi_annual | decimal | USD/year | Conditional | Approved trailing or annualized NOI definition |
| property_value | decimal | USD | Conditional | Most recent eligible collateral value |
| valuation_date | date | Date | Conditional | Effective date of property value |
| valuation_type | category | appraisal/evaluation/indexed/other | Conditional | Valuation basis |
| cap_rate | decimal | Fraction | Derived | NOI divided by value under approved definitions |
| ltv | decimal | Ratio | Derived | Approved exposure divided by eligible value |
| dscr | decimal | Ratio | Derived | Approved NOI divided by debt service |
| debt_yield | decimal | Ratio | Derived | Approved NOI divided by loan balance |

# 5. Performance and outcome fields

| Field | Type | Unit/domain | Requirement | Definition and control |
|---|---|---|---|---|
| days_past_due | integer | Days | Required | Contractual delinquency at as-of date |
| nonaccrual_flag | boolean | true/false | Required | Nonaccrual status |
| default_flag | boolean | true/false | Derived | Approved qualifying first-default indicator |
| default_date | date | Date | Conditional | Earliest approved trigger date |
| default_trigger | category | Approved taxonomy | Conditional | Trigger establishing default |
| cure_date | date | Date | Conditional | Date approved cure conditions are satisfied |
| payoff_date | date | Date | Conditional | Full repayment date |
| resolution_date | date | Date | Conditional | Workout resolution date |
| ead_at_default | decimal | USD | Conditional | Approved exposure immediately before/at default |
| recovery_amount | decimal | USD | Conditional | Gross recovery cash flow amount |
| recovery_date | date | Date | Conditional | Recovery cash-flow date |
| recovery_type | category | Approved taxonomy | Conditional | Principal, collateral, guarantee, or other recovery |
| workout_cost | decimal | USD | Conditional | Directly attributable workout expense |
| workout_cost_date | date | Date | Conditional | Expense cash-flow date |
| realized_lgd_raw | decimal | Unbounded ratio | Derived | Diagnostic discounted workout LGD before production bounds |
| unresolved_default_flag | boolean | true/false | Derived | Default lacks approved resolution by cutoff |

# 6. Market, macroeconomic, and scenario fields

| Field | Type | Unit/domain | Requirement | Definition and control |
|---|---|---|---|---|
| economic_series_id | string | Source series | Required | Stable macro or market series identifier |
| geography_code | string | National/state/MSA | Required | Series geography |
| reference_date | date | Date | Required | Period represented by observation |
| publication_date | date | Date | Required | Initial publication date |
| vintage_date | date | Date | Required | Data revision vintage used |
| economic_value | decimal | Series-specific | Required | Value with transformation and units recorded |
| scenario_id | string | Versioned key | Required | Approved or proposed scenario identifier |
| scenario_horizon | integer | Quarter | Required | Forecast quarter from reporting date |
| scenario_weight | decimal | `[0,1]` | Required | Weight; sums to one by reporting run |

# 7. Modeled outputs

| Field | Type | Unit/domain | Requirement | Definition and control |
|---|---|---|---|---|
| conditional_pd | decimal | `[0,1]` | Required | Hazard conditional on survival to interval start |
| marginal_pd | decimal | `[0,1]` | Required | Probability mass assigned to interval |
| cumulative_pd | decimal | `[0,1]` | Required | Sum of marginal PD through horizon |
| projected_lgd | decimal | Approved bounds | Required | Scenario/horizon loss severity |
| projected_ead | decimal | USD | Required | Finite nonnegative horizon exposure |
| discount_factor | decimal | `(0,1]` normally | Required | Approved factor and convention |
| expected_loss | decimal | USD | Required | Marginal PD × LGD × EAD × discount factor |
| model_version | string | Version key | Required | Component artifact version |
| feature_version | string | Version key | Required | Feature specification version |
| run_id | string | Unique key | Required | Reproducible execution identifier |

# 8. Mandatory contract tests

- Composite keys are unique at their declared grain.
- Required keys and dates are non-null and parseable.
- Balances and commitments are finite and reconcile under approved tolerances.
- Percentages, probabilities, and categorical values obey declared domains.
- Availability dates do not exceed prediction dates for model inputs.
- Outcome cash flows reconcile to source workout records.
- Macro joins have declared geography and frequency behavior.
- Every exclusion and imputation produces a retained reason or indicator.
- Output probabilities, EAD, scenario weights, and expected loss satisfy the
  mathematical controls in the development specification.

