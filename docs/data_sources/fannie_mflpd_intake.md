---
title: "Fannie Mae Multifamily Loan Performance Data Intake Specification"
status: "Controlled working draft"
version: "0.1 proposed"
as_of_date: "2026-09-01"
---

# 1. Development population

Fannie Mae Multifamily Loan Performance Data (MFLPD) is the proposed primary
development source for the initial multifamily CRE study. Fannie Mae reports
that the current dataset covers loans acquired from January 1, 2000 through
March 31, 2026, contains more than 73,000 loans, and represents over 89 percent
of acquisitions during that period. The main file has 62 attributes and one
record per loan and reporting month. A separate annual DSCR file joins by Loan
Number.

This population is not representative of all CRE. Results must be labeled
`Fannie Mae multifamily` and must not be generalized to office, retail,
industrial, hotel, construction, or all bank CRE without external evidence.

# 2. Required user-supplied files

The full data require a registered Data Dynamics account and acceptance of
Fannie Mae's terms. The user downloads these files to a local directory outside
Git control:

1. MFLPD Main File.
2. Historical Annual DSCR File.
3. MFLPD Glossary and File Layout.
4. Statistical Summary for the same release.
5. Credit Events and Loss Sharing Quick Reference Guide.
6. Terms and Conditions effective for the download.

Raw and derived loan-level data must not be committed or redistributed. The
repository stores only code, schemas, checksums, aggregate diagnostics that
meet the terms, and synthetic test data.

# 3. Snapshot manifest

Each quarterly release receives an immutable snapshot ID. The manifest records
download timestamp, release-through date, source page, terms version or capture,
file names, byte sizes, SHA-256 checksums, detected encoding/delimiter, row
counts, distinct loan counts, minimum/maximum reporting dates, and statistical-
summary reconciliation.

Fannie Mae states that quarterly releases may add or remove loans, correct
prior performance, change modified terms, and revise lifetime net credit loss.
Therefore a new download never overwrites an earlier snapshot.

# 4. Initial source-to-target mapping

| MFLPD concept | Proposed target/use | Treatment |
|---|---|---|
| Loan Number | `loan_id` | Stable source key; pseudonymize only in exported diagnostics |
| Reporting Period Date | monthly observation date | Retain monthly grain; derive quarter only after outcome creation |
| Acquisition/Note Date | acquisition/origination timing | Confirm distinction in glossary |
| Maturity Date at Acquisition / Current | contractual/current maturity | Preserve both and modification timing |
| Original/Acquisition/Current UPB | original/current balance and EAD path | Reconcile units and nonnegative bounds |
| Interest and amortization fields | contractual EAD and refinance features | Separate static acquisition from ongoing terms |
| Acquisition LTV, Underwritten DSCR | acquisition risk features | Do not treat as current values |
| Historical Annual DSCR | time-varying operating feature | Apply annual availability rule; no forward fill before publication |
| Property type, state, ZIP and MSA | segmentation/geography | Version geography; Fannie notes geocodes may change |
| Physical Occupancy | acquisition feature | Do not label as monthly occupancy |
| Loan Payment Status, Delinquency UPB, SDQ | PD state/outcome candidates | Map only after glossary and timing review |
| Ever 60+ Days Delinquent | diagnostic | Prohibited as a pre-event predictor because it leaks future history |
| Modification fields | time-varying feature/competing state | Available only from reported effective period |
| Liquidation/Prepayment Code and Date | payoff/default/resolution/competing exit | Distinguish voluntary, default-related, dissolution, conversion and repurchase |
| Credit Event Date and Type | default/event outcome candidate | Definition remains proposed until reviewed |
| Default Amount | LGD denominator/EAD-at-default candidate | Reconcile to balance and credit-event guidance |
| Lifetime Net Credit Loss Amount | LGD numerator candidate | Snapshot-varying; loss-sharing and recovery treatment required |
| Foreclosure Value and Sale Price | collateral/LGD diagnostics | Event-dated; never used as pre-default PD features |
| Loss Sharing Type/Percentage | LGD feature and population control | Evaluate Fannie-versus-lender allocation and servicing transfer |

# 5. Outcome construction rules to approve

## 5.1 PD

The primary candidate event is first qualifying Credit Event Date/Type, with
separate sensitivity definitions for 60+ day delinquency, serious delinquency,
foreclosure, deed-in-lieu, discounted payoff, and third-party sale. Prepayment,
maturity payoff, dissolution, repurchase, substitution, ARM conversion, and
loss-free observation end are competing exits or censoring states—not defaults
unless the approved definition says otherwise.

Fannie Mae notes that MFLPD payment status is one reporting month earlier than
the comparable DUS Disclose status. The model time index must use MFLPD's own
Reporting Period Date and may not mix the two sources without an alignment
test.

## 5.2 LGD

The initial candidate is `Lifetime Net Credit Loss Amount / Default Amount`.
It is not approved until the credit-event/loss-sharing guide establishes sign,
scope, loss allocation, timing, recoveries, expenses, and denominator meaning.
Loss values may change in later releases, so LGD requires a resolution or
seasoning rule and vintage-aware sensitivity. Missing loss is not zero loss.

## 5.3 EAD

For ordinary fully funded loans, EAD begins as current UPB projected through
contractual amortization and competing prepayment/default. Default Amount and
current UPB are reconciled at the event date. Credit Facilities and supplemental
loans require separate treatment because commitments, borrow-up capacity, and
cross-collateralized/cross-defaulted relationships may be incompletely
identified. If limits or commitments are unavailable, conversion-factor EAD is
out of scope.

# 6. Mandatory intake checks

- File checksums and statistical-summary control totals reconcile.
- Loan/reporting-month keys are unique or duplicates have documented rules.
- Monthly records are ordered, contiguous gaps are flagged, and dates are valid.
- Static fields are stable except attributes Fannie identifies as revisable.
- Current UPB is finite/nonnegative and reconciles across adjacent periods.
- Terminal codes are exclusive and no post-terminal performance is silently used.
- Credit-event, foreclosure, liquidation, and loss dates obey plausible order.
- Event and loss availability prevent leakage into pre-event features.
- Snapshot-to-snapshot additions, removals, corrections, and loss revisions are quantified.
- Population counts and balances reconcile to Fannie's Statistical Summary.
- Raw data paths and credentials are absent from Git history.

# 7. References and access constraint

- [Fannie Mae MFLPD landing page](https://capitalmarkets.fanniemae.com/credit-risk-transfer/multifamily-credit-risk-transfer/multifamily-loan-performance-data)
- [Multifamily Data Dynamics FAQs](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-faqs.pdf)

Access is free after registration, but Fannie Mae states that its terms prohibit
third-party distribution and external commercial use without express written
consent. Permitted use and publication of derived results require review before
data acquisition is treated as approved.

