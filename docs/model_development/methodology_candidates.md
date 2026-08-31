---
title: "CRE Expected Loss Methodology Candidates"
status: "Controlled working draft"
version: "0.1 proposed"
as_of_date: "2026-08-31"
---

# 1. Selection principle

No method in this document is approved or selected. Each component begins with
a transparent benchmark. A more complex primary or challenger must demonstrate
stable improvement, conceptual coherence, implementation reproducibility, and
monitorability. Final holdout data must not be used to choose features or tune
methods.

# 2. PD candidates

| Role | Candidate | Strengths | Principal risks | Minimum evidence |
|---|---|---|---|---|
| Benchmark | Segment/vintage quarterly default rates with smoothing | Transparent and auditable | Sparse cells; limited borrower differentiation | Exposure and count rates, uncertainty, temporal stability |
| Proposed primary | Discrete-time logistic or complementary-log-log hazard | Natural quarterly survival treatment; interpretable | Functional-form and proportional-effect limits | Calibration, discrimination, censoring, horizon, segment and time tests |
| Challenger | Penalized hazard with nonlinear splines/interactions | Controls instability while allowing nonlinearity | Tuning and interpretation complexity | Nested temporal tuning and stable incremental benefit |
| Research challenger | Gradient-boosted survival/hazard model | Flexible interactions and nonlinearities | Calibration, explainability, leakage and implementation risk | Material out-of-time gain, calibration, explanations, stress behavior |

Candidate PD models must use the same outcome, risk set, partitions, observation
weights, and point-in-time features. Comparisons include ROC-AUC and precision-
recall where informative, Brier/log loss, observed-to-expected ratios,
calibration curves, survival consistency, uncertainty, and segment/vintage
behavior. No single metric determines selection.

# 3. LGD candidates

| Role | Candidate | Strengths | Principal risks | Minimum evidence |
|---|---|---|---|---|
| Benchmark | Collateral value less haircuts, costs, and senior claims | Economic transparency; useful under sparse workouts | Valuation staleness and haircut judgment | Backtest to resolved cases and haircut sensitivity |
| Simple empirical | Segment mean/median discounted workout LGD with shrinkage | Stable and explainable | Masks case heterogeneity | Resolution, segment, cycle, and uncertainty analysis |
| Proposed primary | Two-part positive-loss probability plus conditional severity | Handles zero-loss mass and severity separately | Selection/censoring and recombination complexity | Out-of-time calibration, tail behavior, unresolved-case treatment |
| Challenger | Fractional/bounded regression or tree ensemble | Flexible conditional severity | Bounds may hide diagnostic losses; overfit | Raw-versus-bounded reconciliation and stable benefit |

All methods use the same cash-flow definition and cutoff. Unresolved defaults
require censoring-aware, resolution-model, or conservative sensitivity
treatment. Downturn behavior must arise from explicit collateral, cash-flow,
liquidity, or duration channels rather than an unexplained additive factor.

# 4. EAD candidates

| Role | Candidate | Strengths | Principal risks | Minimum evidence |
|---|---|---|---|---|
| Benchmark | Contractual amortization and balloon schedule | Deterministic and reconcilable | Omits behavioral prepayment and modification | Exact contractual cash-flow reconciliation |
| Proposed term-loan primary | Contractual projection plus calibrated prepayment/maturity behavior | Better expected balance path | Behavior varies by cycle and segment | Vintage/out-of-time error and stability |
| Future-funding primary | Utilization or credit-conversion model by facility state | Captures expected draws | Sparse construction/revolver histories | Draw history, limits, bounds, and segment support |
| Challenger | Competing prepayment/default/utilization model | Coherent behavioral exits | Higher implementation complexity | Material improvement and horizon consistency |

Separate methodologies are required when contractual structures differ
materially. A statistical EAD component must not override known contractual
limits without an approved explanation and control.

# 5. Scenario and transmission candidates

| Candidate | Description | Evaluation |
|---|---|---|
| Direct macro terms | Macro/property variables enter PD, LGD, or EAD equations | Sign, lag, stability, multicollinearity, scenario sensitivity |
| Structural property bridge | Scenario paths change rent, vacancy, NOI, cap rate, value, DSCR and LTV before risk estimates | Bridge accuracy, coherence, double counting, sensitivity |
| Segment calibration | Scenario-conditioned multipliers or calibration by segment | Empirical basis, bounds, cyclicality, governance |
| Explicit overlay | Separately governed adjustment for unmodeled risk | Trigger, evidence, reversibility, approval, backtest, double-count test |

The proposed preference is an explicit property bridge where data support it,
supplemented by direct terms or controlled calibration. Overlay is not a
permanent substitute for model repair.

# 6. Aggregation and discounting

Expected loss is deterministic once marginal PD, LGD, EAD, discount factor,
and scenario are fixed. Alternative formulas are not candidates. Candidate
discount conventions may be assessed only against the approved intended use;
the selected convention and rate source remain `Open`.

# 7. Predeclared comparison record

For every candidate, development records artifact/configuration version,
sample and partitions, features, hyperparameters, fitting method, seed,
calibration, metrics with uncertainty, sensitivities, limitations, operational
requirements, and selection disposition. Selection rationale must explain why
the retained method is fit for the approved use and why rejected alternatives
were not retained.

