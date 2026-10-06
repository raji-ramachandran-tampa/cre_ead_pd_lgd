# DSCR availability evidence audit — October 5, 2026

Lifecycle: model development. Audience: developers, owners and research reviewers. Status: actual historical availability not established; no candidate selection or change to fitted results.

## Verified findings

The raw historical annual DSCR CSV has exactly three fields: Loan Number, Year and Year DSCR. The standardized file retains those fields. Fannie Mae defines Year as the year associated with the fiscal year-end statement, not a publication date. DSCR before 2007 is unavailable in MFLPD. [Glossary](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/mflpd-glossary-file-layout.pdf).

Fannie Mae's December 18, 2020 announcement stated that the new public historical annual DSCR file would debut in late January 2021, and be updated quarterly with the most recent annual value available. This establishes the announced public introduction period, not the actual first publication date of every observation. [Announcement](https://capitalmarkets.fanniemae.com/mortgage-backed-securities/multifamily-loan-performance-data-be-enhanced-additional-data-attributes-and-accompanying-new-file).

The local raw source contains only release 2026Q1. No earlier release series is present to reconstruct first appearance or revisions. Zero row-level publication dates were verified.

## Model impact

| Primary two-year lag experiment | Total loans | Prediction anchors before 2021 | Before-2021 anchors with DSCR |
|---|---:|---:|---:|
| Pre-disposition update | 672 | 657 | 410 |
| Before first observed SDQ | 659 | 650 | 381 |

January 1, 2021 is an optimistic boundary used only to count observations clearly preceding the introduction year. It is not an asserted launch date; observations after it remain unverified. Neither a one-year nor a two-year reference-year lag establishes public availability. Historical feature analyses are retrospective research from a later snapshot, not operational point-in-time validation.

The public-file launch does **not** prove lenders lacked financial statements earlier. Lender/servicer receipt, calculation and approval dates are distinct from public release dates. Servicing deadlines also do not establish actual receipt or public disclosure for a particular observation. Do not assume fiscal years end on December 31 merely from the annual Year field.

This limitation also applies to PD candidates using historical annual DSCR. It does not change fitted metrics or by itself show that macro-release alignment is wrong; it limits interpretation of the overall historical feature set.

## Required evidence and controls

For public-data historical forecasting: dated archived quarterly releases, verified release timestamps and first appearance of each loan/year/value; track later revisions separately. First appearance in a complete archive provides an observed availability bound, not necessarily lender receipt.

For lender forecasting: actual fiscal-period end, statement receipt, review/calculation and model-usable availability dates. Use only observations available by prediction date. Different intended users imply different information sets.

Until such evidence exists, retain static/simple and no-annual-DSCR baselines. Treat DSCR challengers as retrospective sensitivities; do not select the one-year lag from its better accuracy. No automatic deletion of loans, invented publication dates, new default definition or model approval.

## Reproduction

```powershell
python scripts/lgd_dscr_availability_audit.py --fannie-root <external Fannie root> --output <new immutable audit directory>
```

External version: lgd-dscr-availability-audit-v0.1.0. report.json contains aggregate evidence, raw header check, release inventory, source hashes and conclusions. Restricted loan/date evidence remains in availability_audit.parquet outside Git. Existing output fails rather than overwriting. The audit does not refit or modify any model or source file.

## Archive search and additional release-timing evidence

Reviewed the official MFLPD page, Data Dynamics FAQ, Data Dynamics portal and DUS Disclose Reports/Data Archive on October 5, 2026. No dated historical annual-DSCR snapshots were retrieved. The Data Dynamics browser reached its email/password login page; archive availability after authentication remains unverified. DUS Disclose's public archive page displayed its description but no downloadable categories in the inspected view; this does not establish that no archive exists.

The April 2023 Data Dynamics FAQ, Q17, gives a concrete example: first-quarter performance information would be published by July 14. Do not equate the monthly Reporting Period Date with public availability. Q18 also describes changes in acquisitions, servicing records and lifetime losses across releases. This extends the public-data timing limitation beyond annual DSCR to monthly-history predictors. Preserve lender operational reporting and public release information sets separately.

Reference: https://capitalmarkets.fanniemae.com/media/7756/display . A documented release schedule is not proof of a particular row's first appearance, completeness or actual release timestamp.

Archive evidence to collect after sign-in: each available full quarterly release, coverage quarter, actual publication date/evidence, raw-file checksum and retrieval timestamp. Compare loan/year/value across releases to track first observed appearance and revisions. Never treat a statement fiscal year, ZIP member timestamp, download time or an announced schedule as an actual row publication date.


## Authenticated portal follow-up — October 5, 2026

After the user signed in, inspected HP Download Data > Multifamily Loan Performance Data and HP Messages. The multifamily page exposed one Main File and one Historical Annual Debt Service Coverage Ratio File, without an older-release/vintage selector in the inspected view. Single-family quarterly downloads are a different dataset and cannot supply multifamily DSCR vintages. No older multifamily DSCR release was retrieved.

Downloaded the available annual DSCR ZIP to the user's Downloads folder. It is byte-for-byte identical (SHA256 comparison) to the existing raw/2026Q1/Multifamily_DSCR.zip; its CSV content hash also matches. It contains 316,304 data rows and the same three fields. The downloaded copy adds a retrieval observation, not new historical publication metadata; existing raw data were not overwritten.

HP Messages did not supply an MF annual DSCR vintage archive or row-level availability dates in the inspected list. The Data Refresh Calendar describes scheduled dashboard updates and explicitly allows publication delays; it does not establish actual dates for each annual observation. Reference: https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/data-dynamics-data-refresh-calendar.pdf . The current portal's lack of a selector does not prove that Fannie Mae or an authorized source cannot provide archived releases through another channel.

Result: authentication blocker resolved, but the availability evidence gap remains. No fitted model or metric changed. Obtain archived source vintages from an authorized source or actual lender receipt records before point-in-time DSCR claims.
