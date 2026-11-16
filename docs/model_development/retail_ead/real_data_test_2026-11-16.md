# Retail EAD/CCF real-data feasibility test — November 16, 2026

Lifecycle: development. User authorized testing actual supplied files. Status:
exploratory delinquency-proxy targets and simple benchmarks executed,NOT a selected
or independently validated model of material contractual defaults. Institutional
owner/approval TBD. Separate retail branch;CRE models and paper unchanged.

## Target and pairing experiment

Compare first observed90DPD using SK_DPD and small-debt-tolerantSK_DPD_DEF.
3/6/12month exact anchors must be Current under the respective delinquency measure,
with complete intervening monthly observations and nonnegative exposure inputs.
First-record events leftcensored,missing anchors/gaps and credit balances remain
flagged in saved pairs,not silently filled. ApplicationTARGET never used.
Relative months do not identify calendar dates or permit calendarOOT testing.
AMT_BALANCE is reported monthly balance,not verified principal+interest decomposition.

Raw90DPD1806 accounts,tolerance90DPD39. All raw pair rows5418,tolerance117 potential
horizon pairs before exclusions;horizons share accounts and are not independent.
Current/complete-history eligible counts:

| Event proxy | Horizon | Eligible EAD pairs | Positive anchor limit | Defined CCF pairs | Model status |
|---|---|---:|---:|---:|---|
| Raw90DPD | 3months | 34 | 24 | 24 | Sparse:18train/6heldout,skip |
| Raw90DPD | 6months | 1325 | 1313 | 1272 | Exploratory fit1053train/260heldout |
| Raw90DPD | 12months | 1408 | 1406 | 1323 | Exploratory fit1112train/294heldout |
| Tolerance90DPD | 3months | 0 | 0 | 0 | No eligible pairs |
| Tolerance90DPD | 6months | 12 | 12 | 8 | Sparse:12train/0heldout,skip |
| Tolerance90DPD | 12months | 15 | 15 | 12 | Sparse:11train/4heldout,skip |

Fixed minimum before fitting:60training groups and20heldout groups. No model search
or threshold relaxation based on sample/performance. Split application-link groups
by deterministicSHA256modulo5 (20%expected),same mapping across horizons/proxies.
This holds linked accounts together but does not prove ultimate borrower independence.
Not chronological validation. Applicants' historical cards are selected relative to
current loan applications,not an unrestricted representative cardholder panel.

## Simple benchmark test

Compare current balance hold,trainingmeanEAD,and trainingmean(EAD/anchorlimit)
scaled by each heldout limit. Fit regularized log-link PoissonRegressor(alpha1)
to EAD/anchorlimit;prediction nonnegative,not a CCF. Training-only median imputation
and scaling. Inputs log startingbalance/limit,utilization,prior3month balance change,
mean drawings and mean payments,all at/before anchor. No future event balance as input.

| Raw proxy horizon | Heldout cases | Hold MAE | MeanEAD MAE | MeanEAD/limit MAE | Regression MAE |
|---|---:|---:|---:|---:|---:|
| 6months | 260 | 23485.20 | 5644.57 | 4169.71 | 4221.37 |
| 12months | 294 | 55291.01 | 6154.97 | 4744.19 | 4749.84 |

MAE is in raw source amount units,currency/anonymization not independently verified.
Regression does NOT beat the simple limit-ratio benchmark. Aggregate absolute
error/SUM eventbalance is293.70%at6months and181.71%at12months for regression;
ratios can exceed100%,not accuracy percentages. Large errors reflect distribution
and small event balances;not meaningful bank-loss predictive performance.

## CCF behavior

CCF=(eventbalance-startbalance)/(startlimit-startbalance),only positive undrawn
anchors;fullydrawn/overlimit retainEAD rows with undefinedCCF. Negative and>1
CCFs retained:raw6month754negative/10above1 of1272;raw12month1127negative/12above1
of1323. MedianCCFraw6month-0.00308,12month-0.45989. This is an observed net exposure
change,not a pure draw fraction. It cannot be repaired by automatic[0,1]clipping.

TrainingmeanCCF benchmark evaluated on positive-undrawn heldout subsets only.
It generates225 negative EAD forecasts among2566month cases and248 among278
12month cases. Those forecasts are economically invalid and explicitly reported,
not clipped or counted as an acceptable candidate. Near-zero undrawn denominators
and heterogeneous balance paths require separate handling. DirectEAD avoids that
denominator but does not fix missing/default semantics.

Tolerance90DPD eligible subsets have medianCCF1.08189at6months(8defined) and
1.15229at12months(12defined),with4/10above1. Tiny samples and different event
materiality prevent extrapolation to raw90DPD or a bank portfolio.

## Interpretation and recommendation

The pipeline works, but this source is NOT established as suitable primary data
for a defensible material-defaultEAD/CCF model. RawDPD yields more cases yet many
small-debt events ignored by tolerance;the latter leaves too few Current-anchor
cases for robust modeling. This is a substantive data-target feasibility finding,
not evidence that regression or revolvingEAD modeling in general is impossible.

Do not train an advanced model simply to compensate for weak labels. Preserve this
as methodological feasibility evidence;inspect balance composition/materiality,
source tolerance definition and alternative access to genuine revolving default
panels. Do not redefine default solely to manufacture sample size. No CRE/retail
pooling,model approval,economicEL or true bank-default performance claim.

## Reproduction and artifacts

python -m cre_expected_loss.retail_ead.experiment --root <HOME_CREDIT_ROOT>
--output <new-external-directory>. External immutable
retail-ead-proxy-test-v0.1.0 has all_proxy_pairs.parquet,held_out_predictions.parquet,
models.joblib,report.json. Hashes for source,dictionary and experiment;groupcounts,
all exclusion reasons,benchmarks,CCF failures and limitations recorded. Serialized
predictions reproduce554heldout horizon cases withinrtol1e-12/atol1e-8. No source
file modified,no loan IDs/rawrows/modelbinaries inGit. Synthetic tests verify
historical feature cutoff,stable group split and nonnegative target-free scoring.
New code/test lint and full-suite results recorded below. Existing models remain
frozen. This is a research prototype,not independent validation.

Verification November16:132 tests passed,five Pandoc skips;one existing pandas
deprecation warning. New experiment/test lint passes. Source implementation hash
verified against executed artifact;554heldout horizon predictions reload-match.
