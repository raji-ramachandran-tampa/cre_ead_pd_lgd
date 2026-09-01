---
title: "Classical, Bayesian, and Machine-Learning Comparison Plan"
status: "Controlled working draft"
version: "0.1 proposed"
as_of_date: "2026-09-01"
population: "Fannie Mae multifamily loans"
---

# 1. Research objective

The study compares classical, Bayesian, and machine-learning methods for PD,
LGD, and EAD on identical Fannie Mae multifamily samples, definitions,
features, time partitions, and evaluation periods. The purpose is to show the
incremental value and governance cost of each family. It does not assume that
the most complex method is superior or that industry practice proves fitness.

Classical methods are mandatory benchmarks because they are transparent,
stable, readily independently reproduced, and often proportionate to sparse
default/loss data. Bayesian methods test whether partial pooling and quantified
parameter uncertainty improve sparse-segment estimates. Machine learning tests
whether nonlinearities and interactions add stable out-of-time value.

# 2. Common experimental controls

- Monthly loan-period risk set with first event, competing exit, and censoring.
- Chronological development, validation, and untouched final test periods.
- Loan grouping across all partitions; no random row leakage.
- One versioned outcome definition and feature snapshot per experiment.
- Acquisition-only and point-in-time features clearly distinguished.
- Identical exposure/sample weights unless method-specific weighting is declared.
- Hyperparameter and prior selection use development/validation data only.
- Final test set is evaluated once after candidates are frozen.
- Results shown overall and by vintage, property type, geography, loan age,
  leverage, DSCR, product, and stress period where sample size permits.
- Complexity is selected only for material, stable, explainable benefit after
  calibration, uncertainty, implementation, monitoring, and reproducibility cost.

# 3. PD comparison

| Family | Proposed method | Output | Key strengths | Key risks |
|---|---|---|---|---|
| Classical benchmark | Discrete-time logistic and complementary-log-log hazard with regularized/selected terms | Monthly hazard, marginal and cumulative PD | Interpretable, survival-consistent, reproducible | Linear/additive restrictions; sparse segments |
| Bayesian | Hierarchical discrete-time hazard with partial pooling for property type, geography and vintage | Posterior hazard/PD distribution and credible intervals | Shrinkage and explicit parameter uncertainty | Prior sensitivity, computation, convergence |
| Machine learning | Gradient-boosted monthly hazard followed by out-of-time probability calibration | Calibrated hazard and PD term structure | Nonlinearities and interactions | Leakage, instability, calibration, explanation burden |

PD evaluation includes log loss, Brier score, calibration slope/intercept and
curves, observed-to-expected ratios, ROC-AUC and precision-recall where useful,
time-dependent discrimination, cumulative-PD coherence, subgroup error,
economic sensitivity, and uncertainty. Bayesian evaluation additionally
includes prior sensitivity, chain convergence, effective sample size, posterior
predictive checks, and interval coverage.

# 4. LGD comparison

| Family | Proposed method | Output | Key strengths | Key risks |
|---|---|---|---|---|
| Classical benchmark | Two-part logistic positive-loss model plus GLM/fractional or transformed severity | Expected loss severity | Transparent decomposition; familiar diagnostics | Boundary/tail fit and unresolved selection |
| Bayesian | Hierarchical two-part model with segment/vintage partial pooling | Posterior LGD distribution | Stabilizes sparse losses; quantifies uncertainty | Prior and likelihood sensitivity |
| Machine learning | Boosted classifier plus boosted severity regressor, recombined and calibrated | Expected LGD | Flexible interactions and tails | Overfit, incoherent tails, weak uncertainty |

All methods use the same approved loss numerator/denominator, resolution cutoff,
loss-sharing treatment, and missing/unresolved population. Compare MAE, RMSE,
mean calibration, zero-loss classification, quantile/tail error, subgroup bias,
temporal stability, and sensitivity to revised lifetime losses. Raw diagnostic
LGD remains visible before any output bounds.

# 5. EAD comparison

| Family | Proposed method | Output | Key strengths | Key risks |
|---|---|---|---|---|
| Classical benchmark | Contractual balance projection with classical prepayment/competing-risk adjustment | Horizon UPB/EAD | Exact cash-flow basis; interpretable | Limited behavioral flexibility |
| Bayesian | Hierarchical balance-runoff/prepayment model with product and vintage pooling | Posterior EAD path | Stable sparse-segment estimates and intervals | Model complexity and convergence |
| Machine learning | Boosted balance-factor or runoff model with competing-exit component | Horizon EAD | Nonlinear behavior and interactions | Bounds, extrapolation and reconciliation |

For Fannie fully funded loans, EAD is projected balance rather than a generic
commitment conversion factor. Credit Facilities are separated unless commitment
and limit data support future-draw modeling. Evaluation includes horizon-level
MAE/RMSE, weighted percentage error, balance reconciliation, nonnegative and
limit bounds, maturity/balloon behavior, prepayment performance, subgroup bias,
and temporal stability.

# 6. Integrated expected-loss comparison

Each method family produces loan-horizon-scenario components, but mixed-family
combinations are also tested to identify which component creates improvement.
Every result uses:

`EL = marginal PD × LGD × EAD × discount factor`

The comparison reports component error and integrated loss error separately.
Scenario-specific estimates are retained before weighting. Statistical benefit
must not be confused with economic materiality; both are reported with bootstrap
or posterior uncertainty as appropriate.

# 7. Selection scorecard

| Dimension | Classical | Bayesian | Machine learning |
|---|---|---|---|
| Conceptual fit | To be evidenced | To be evidenced | To be evidenced |
| Out-of-time predictive performance | To be measured | To be measured | To be measured |
| Calibration | To be measured | To be measured | To be measured |
| Stability and sensitivity | To be measured | To be measured | To be measured |
| Uncertainty quality | Sampling intervals | Posterior distribution | Bootstrap/conformal or documented limitation |
| Interpretability | Expected strong | Moderate with posterior summaries | Requires explanations and constrained diagnostics |
| Implementation/reproduction | Expected simplest | Sampling controls required | Pipeline/tuning controls required |
| Monitoring burden | Expected lowest | Posterior and drift monitoring | Drift, calibration and explanation monitoring |
| Final disposition | Not selected | Not selected | Not selected |

No numeric weights or acceptance thresholds are assigned until approved. A
champion may differ by PD, LGD, and EAD. A complex challenger can remain a
monitoring benchmark even when the classical method is selected for use.

# 8. Required artifacts

Each family produces versioned configuration, fitted artifact, seed, environment,
training log, predictions at the common evaluation grain, metrics with
uncertainty, calibration and stability plots, sensitivity results, limitations,
implementation tests, and a reproducible candidate-comparison record. Bayesian
posterior draws and ML tuning histories are controlled artifacts, not notebook-
only outputs.

# 9. Stop conditions

- Do not compare methods until outcome and point-in-time data tests pass.
- Do not fit segment effects with insufficient events without pooling or restriction.
- Do not claim Bayesian superiority solely from credible intervals.
- Do not claim ML superiority from training or randomly split performance.
- Do not model LGD if loss-sharing and revised lifetime loss are unresolved.
- Do not model future-draw EAD without commitments or limits.
- Do not describe any candidate as validated, approved, or production-ready.

