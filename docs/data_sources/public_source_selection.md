---
title: "CRE Expected Loss Public-Data Source Selection"
status: "Controlled working draft"
version: "0.1 proposed"
as_of_date: "2026-09-01"
lifecycle_stage: "Model development — data sourcing"
---

# 1. Decision and intended use

The proposed initial foundation is Fannie Mae Multifamily Loan Performance Data
for a controlled multifamily CRE study. SEC EDGAR Form ABS-EE commercial
mortgage-backed securities data is retained as a broader-CRE challenger,
enriched with
official macroeconomic and regional series and benchmarked to aggregate bank
and commercial-property indicators. This selection supports feasibility,
economic expected-loss research, benchmark construction, and data-gap
assessment. It does not yet support production, CECL, capital, or formal stress
use.

The selected sources cannot by themselves create a complete population of bank
CRE loans. Public CMBS differs from bank-held CRE by underwriting, structure,
size, geography, servicing, and securitization eligibility. Workout expenses,
guarantees, future funding, modifications, and final recoveries may be missing
or inconsistently observable. Those limitations must be quantified before any
model is fitted.

# 2. Selection criteria

Sources were assessed for authority and provenance, loan/property/outcome
content, point-in-time dates, historical and stressed coverage, geographic and
property granularity, machine readability, revision behavior, stable keys,
terms of use, reproducibility, and expected maintenance burden.

Statuses mean:

- **Selected — primary:** planned foundation for the initial feasibility data.
- **Selected — enrichment:** planned explanatory or scenario variables.
- **Selected — benchmark:** independent aggregate comparison, not loan labels.
- **Conditional:** useful only after terms, field coverage, or methodology
  review.
- **Deferred:** not required for the initial controlled acquisition.

# 3. Selected source register

| ID | Source and authority | Role | Grain/frequency | Status | Principal limitation |
|---|---|---|---|---|---|
| FANNIE-MFLPD | Fannie Mae Multifamily Loan Performance Data | Initial monthly loan/default/loss development foundation | Loan-month plus annual DSCR | Selected — primary, registration required | Multifamily/Fannie population; restricted redistribution; sparse/revised losses |
| SEC-ABS-EE | SEC EDGAR Form ABS-EE Exhibit 102 CMBS asset files | Broader property-type challenger | Asset/reporting period; commonly periodic filings | Selected — secondary | Securitized population; schema/issuer variation; incomplete workout economics |
| FRB-SCENARIO | Federal Reserve supervisory scenario historical and scenario CSV files | National macro and CRE-price history; scenario benchmark | National quarterly and scenario quarter | Selected — enrichment | Supervisory scenarios are not automatically the model's approved scenarios |
| FRED-ALFRED | Federal Reserve Bank of St. Louis FRED/ALFRED | Rates, spreads, macro history, and data vintages | Series-specific | Selected — enrichment | API key; series-specific rights and revisions require review |
| BLS-PUBLIC | BLS Public Data API: LAUS, CES and selected QCEW-derived series | Labor-market and sector demand variables | National/state/MSA; monthly/quarterly | Selected — enrichment | Series definitions and geographic boundaries change |
| BEA-REGIONAL | BEA Regional API | State/county/MSA GDP, income, employment and price parity | Annual/quarterly depending on table | Selected — enrichment | Publication lags and revisions; mixed geographic frequencies |
| CENSUS-BPS | Census Building Permits Survey | Multifamily/residential supply pipeline proxy | National through place/CBSA; monthly/annual | Selected — enrichment | Residential construction proxy, not general CRE inventory |
| FFIEC-CALL | FFIEC Call Report bulk data and MDRM metadata | Bank CRE balances, delinquency and charge-off benchmarking | Institution-quarter | Selected — benchmark | Aggregate institution data; no loan/property outcomes |
| FRB-SLOOS | Federal Reserve Senior Loan Officer Opinion Survey | CRE credit-standard and demand regime indicator | Aggregate survey release | Selected — benchmark | Qualitative aggregate responses; respondent details confidential |
| FHFA-HPI | FHFA House Price Index datasets | Multifamily/residential collateral-market proxy | National/state/MSA/other; monthly/quarterly | Conditional | Single-family index; not a CRE valuation measure |
| BIS-CPPI | BIS commercial property price statistics | National commercial-property-price challenger | Mostly national; frequency varies | Conditional | Source/method comparability and underlying rights vary by series |

# 4. Primary loan-level source: Fannie Mae MFLPD

The intake and outcome requirements are defined in `fannie_mflpd_intake.md`.
The full files require a registered Data Dynamics account and must remain
outside Git. The initial model population is explicitly Fannie Mae multifamily,
not all CRE.

# 5. Secondary loan-level source: SEC ABS-EE

The SEC requires asset data files to be filed as Exhibit 102 to Form ABS-EE.
The SEC's guidance states that performance-related information includes
scheduled and actual collections and delinquency information, and amended
asset data for the same reporting period must be re-filed as a complete Exhibit
102 rather than a partial patch. Percent, rate, and ratio fields are reported as
decimals. These controls make the filing and acceptance timestamps, accession,
period of report, amendment status, and exhibit checksum essential lineage
fields.

## 5.1 Proposed acquisition pattern

1. Discover `ABS-EE` and `ABS-EE/A` filings from EDGAR daily or full indexes.
2. Retain filer CIK, accession, filing date, acceptance timestamp, period of
   report, form, and amendment relationship.
3. Fetch the filing index and Exhibit 102 XML from the SEC archive using a
   declared user agent and compliant request rate.
4. Store the untouched filing and exhibit in an immutable snapshot directory.
5. Hash each file and parse against a versioned SEC schema/tag dictionary.
6. Preserve original values and null/omission indicators before standardizing.
7. For duplicate reporting periods, apply an explicit amendment-precedence rule
   while retaining every version.
8. Construct loan-property-quarter observations only after key, relationship,
   and reporting-period tests pass.

The SEC's public `data.sec.gov` APIs do not require an API key, but automated
access must follow SEC fair-access requirements. The submissions API is useful
for filer history; Exhibit 102 retrieval uses the EDGAR archive structure.

## 5.2 Required feasibility tests

- Count filings, trusts, loans, properties, quarters, and unique relationships.
- Quantify tag availability by schema version, filer, property type, and time.
- Test loan and property key persistence across filings and servicer changes.
- Reconcile balances and asset counts to filing-level totals where available.
- Profile delinquency, nonaccrual-equivalent, modification, liquidation, payoff,
  and resolution indicators without imposing an unapproved default definition.
- Determine whether recovery amounts, liquidation proceeds, expenses, and dates
  can support workout LGD; otherwise restrict LGD to benchmark research.
- Compare CMBS distributions with FFIEC bank aggregates and disclose selection
  bias that cannot be corrected.

# 6. Enrichment and scenario sources

## 6.1 Federal Reserve scenario history

Use the Federal Reserve's downloadable domestic historical and scenario CSV
files as a controlled national scenario benchmark. The published files include
macroeconomic variables and a commercial real estate price index. Preserve the
release year, final/proposed designation, scenario name, jump-off date,
historical/scenario flag, variable dictionary, and retrieval checksum.

These paths are external supervisory scenarios, not approved internal scenario
weights or forecasts. Their use in estimation, sensitivity, or benchmarking
must remain separately identified.

## 6.2 FRED and ALFRED

FRED provides programmatic series observations, while ALFRED adds real-time
periods showing what was originally released and later revised. ALFRED is the
preferred route when a point-in-time vintage is available. Each series requires
its own source, frequency, units, seasonal adjustment, transformation, revision,
and rights review; inclusion in FRED does not erase third-party restrictions.

Initial candidate families are Treasury rates, prime rate, credit spreads,
unemployment, inflation, and national activity. Final series IDs are selected
only after correlation, redundancy, release-lag, and conceptual reviews.

## 6.3 BLS, BEA, and Census

BLS is the preferred labor source for national and geographic employment and
unemployment measures. BEA is the preferred source for regional GDP, income,
and employment aggregates. Census BPS is selected only as a multifamily and
residential supply proxy; it must not be labeled as total office, retail,
industrial, or hotel supply.

Every geographic join requires a versioned CBSA/county/state crosswalk and an
explicit policy for boundary changes. Monthly and annual observations require
an approved quarterly alignment and availability lag.

# 7. Benchmark and conditional sources

FFIEC Call Report bulk data provide quarterly institution-level balance-sheet,
income, and past-due information and are selected to benchmark bank CRE
exposure and performance trends. They cannot create loan-level PD or LGD labels.
Amended bulk files may change after initial publication, so every retrieval is
snapshotted and checksummed with its retrieval date.

SLOOS provides aggregate changes in CRE lending standards and demand. It is a
regime indicator or sensitivity variable, not a loan characteristic.

FHFA HPI is publicly available across long histories and many geographies, but
it measures single-family values. It is conditional for multifamily collateral
sensitivity and prohibited as a direct general-CRE valuation substitute without
empirical support. BIS commercial-property prices are conditional pending
series-level source, methodology, comparability, and rights review.

# 8. Sources not selected for the initial build

Commercial vendor datasets, trustee/servicer portals without stable public
terms, web-scraped listing data, generative-AI outputs, and unattributed
aggregations are not selected. They may be reconsidered through third-party,
licensing, lineage, information-security, and change-management review.

# 9. Proposed acquisition sequence

| Phase | Scope | Completion evidence |
|---|---|---|
| 1 | User-authorized Fannie MFLPD quarterly snapshot and reference materials | Terms record, manifest, raw checksums, statistical-summary reconciliation |
| 2 | Fannie monthly panel and PD/LGD/EAD outcome feasibility | Key persistence, corrections, missingness, events, losses and representativeness report |
| 3 | Common-sample classical/Bayesian/ML benchmark dataset | Frozen outcomes, features, chronological partitions and experiment manifest |
| 4 | Federal Reserve scenario history plus ALFRED/FRED macro pilot | Vintage-aware economic table and release-lag tests |
| 5 | BLS/BEA/Census enrichment and FFIEC/SLOOS benchmarks | Geographic crosswalk, alignment, aggregate comparison and limitations |
| 6 | SEC ABS-EE broader-CRE challenger pilot | Parsed tag inventory, key persistence and population comparison |
| 7 | Source-selection gate | Approved sources, permitted uses, exclusions, unresolved gaps, and component restrictions |

# 10. Approval and stop conditions

Before scale acquisition, the data owner and appropriate Legal/Compliance or
third-party authority must approve permitted use, retention, redistribution,
credentials, and attribution where required. Development must stop or restrict
a component when stable keys, outcome coverage, point-in-time dates, or lawful
use cannot be demonstrated.

No fitted PD, LGD, or EAD model should be selected until the Fannie feasibility
study establishes population coverage and executable outcomes. If credit-event,
loss-sharing, commitment, or balance fields are inadequate, the affected LGD or
EAD comparison remains a benchmark/proxy exercise and the limitation must be
reflected in intended use.

# 11. Authoritative references

- [SEC information for Form ABS-EE filings](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/information-form-abs-ee-filings)
- [SEC EDGAR APIs and bulk data](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [Federal Reserve 2026 stress-test data and documentation](https://www.federalreserve.gov/supervisionreg/dfa-stress-tests-2026.htm)
- [FRED and ALFRED web-service documentation](https://fred.stlouisfed.org/docs/api/fred/alfred.html)
- [BLS Public Data API](https://www.bls.gov/developers/home.htm)
- [BEA Data API](https://apps.bea.gov/api/signup/)
- [Census Building Permits Survey](https://www.census.gov/construction/bps/index.html)
- [FFIEC public bulk-data information](https://cdr.ffiec.gov/public/HelpFiles/WelcomeAdditionalInfo.htm)
- [Federal Reserve SLOOS description](https://www.federalreserve.gov/boarddocs/SnLoanSurvey/about.htm)
- [FHFA HPI datasets](https://www.fhfa.gov/house-price-index?tab=HPI+Datasets)
- [BIS commercial property prices](https://data.bis.org/topics/CPP?m=2646)
