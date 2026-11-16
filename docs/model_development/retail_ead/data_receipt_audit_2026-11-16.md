# Retail source files received and checked — November 16, 2026

User placed HomeCredit_columns_description.csv and credit_card_balance.csv.zip in
external retail_ead root. Both found/readable. ZIP had one expectedCSV,extracted
safely into prepared raw/home-credit-default-risk-2018;dictionary copied there,
original files retained. Source download origin/access terms not independently
verified. No raw or account-level data uploaded to Git. No model fitted.

## Executed schema/quality audit

3,840,312 monthly observations;104,307 card accounts;103,558 linked current sample
loan/application IDs.23 columns;expected fields present. No missingIDs,bad month
indices,nonfinite/missing balance or limit,negative limits,unknownDPD,duplicate
account-month keys or multiple application links per account. Application linkage
does not establish ultimate borrower identity. Negative balances2345 retained as
credit/adjustment cases needing interpretation.1,088,360 rows have no positive
undrawn amount;CCF denominator cannot be used indiscriminately.

48,377 monthly rows rawDPD>=90,representing1806 distinct accounts,not48377 defaults.
Only39 distinct accounts ever have tolerance-adjustedDPD>=90.47,299 raw90DPD rows
have toleranceDPD<90. Nine raw90DPD accounts already satisfy the threshold at first
observation (leftcensoring). First raw90DPD event:1736 positive balances,70 zero,
median207.0225 in raw amount units;38 also tolerance90 at that event. Do not
interpret the remaining raw events automatically as material contractual defaults.

## Dictionary review

219 dictionary rows,23 entries for cardCSV;cp1252 decoding required,original bytes
unchanged. Confirmed balance is monthly previous-credit balance;limit is monthly
card limit;draws,total payments and receivableprincipal are separate fields.
SK_DPD is dayspastdue;SK_DPD_DEF applies tolerance ignoring small debts,not a binary
default flag. MONTHS_BALANCE is relative to current application,-1freshest;range
-96to-1. SK_ID_CURR denotes a loan in the sample,not verified borrower identity.
Currency/anonymization and exact interest/balance components remain unverified.
No calendar OOT/macro alignment or applicationTARGET-to-card-default label join.

## Preliminary candidate-anchor coverage,not final target sample

Raw90DPD1806 event accounts;exact3/6/12month anchors1791/1719/1595. Current anchors
with nonnegative balance/limit and event balance34/1325/1408;positive undrawn
24/1272/1323. These are preliminary counts before complete-gap,censoring and
all model-quality checks. Sparse3month Current anchors reflect timing/definition
constraints;no cohort or model specification selected from these counts.

The substantial raw/toleranceDPD discrepancy is the main next research issue.
Audit materiality and balance composition before choosing a delinquency proxy or
claiming enough meaningful EAD defaults.39 tolerance90 accounts may be too sparse
for complex development/generalization;raw90 sample needs defensible interpretation.
Do not relax default/materiality definition simply to enlarge the sample. No CCF
clipping,synthetic augmentation or fit based on current findings.

## Provenance and next work

External immutable reports:retail-ead-audit-v0.1.0,retail-ead-source-review-v0.1.0,
retail-ead-file-receipt-v0.1.0. Raw CSV SHA256
 a9cdc48900d55131c90f3128b991859aeb94ca1326fb5f4d1624b9fd03782247;
dictionary SHA256eef7665398228a80f7367c9258220c5fbe1038f3f54094244f354d54e2d4fb03.
Existing audited code executed;no new model or full-suite rerun in this step.
Next:raw/tolerance event and balance-materiality review,then decide target
feasibility. Files are technically ready;model target is not yet finalized.
