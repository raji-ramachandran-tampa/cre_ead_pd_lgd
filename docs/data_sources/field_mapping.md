# Provisional public-source field mapping

This mapping identifies plausible source families, not confirmed tag-level
availability. Exact SEC XML tags, FFIEC MDRM items, economic series IDs, and
geographic crosswalks must be versioned after pilot profiling.

| Target field family | Preferred source | Secondary/benchmark | Mapping status | Key qualification |
|---|---|---|---|---|
| Loan and property keys | SEC ABS-EE Exhibit 102 | Filing accession and trust CIK | Pilot required | Test persistence and multi-property relationships |
| Reporting and availability dates | SEC filing metadata and period of report | EDGAR acceptance timestamp | Candidate | Availability cannot precede SEC acceptance |
| Origination, maturity, balance and rate | SEC ABS-EE CMBS asset fields | None public at loan level | Pilot required | Preserve original units and amendments |
| Property type and geography | SEC ABS-EE property fields | Census geographic crosswalk | Pilot required | Version taxonomy and boundary mappings |
| NOI, occupancy, valuation, DSCR and LTV | SEC ABS-EE asset/property fields where reported | FHFA or scenario index only as sensitivity proxy | Pilot required | Definitions and effective dates may differ by filer |
| Delinquency and modification | SEC ABS-EE performance fields | FFIEC aggregate past-due trends | Pilot required | Default definition remains unapproved |
| Payoff, liquidation and resolution | SEC ABS-EE status/performance fields | None | Pilot required | Determine dates and terminal-state reliability |
| Recoveries and workout costs | SEC ABS-EE where present | Collateral benchmark | Major gap risk | Do not infer absent cash flows as zero |
| Bank CRE exposure/performance | Not loan-level public | FFIEC Call Reports | Benchmark only | Institution-quarter aggregate |
| CRE credit standards/demand | Not loan-level public | Federal Reserve SLOOS | Benchmark only | Qualitative aggregate series |
| National CRE price | Federal Reserve scenario historical data | BIS CPPI conditional | Selected/conditional | Definitions and source rights require retention |
| House/residential price | FHFA HPI conditional | Federal Reserve scenario HPI | Proxy only | Not general CRE collateral value |
| Employment/unemployment | BLS API | FRED/ALFRED delivery | Selected | Preserve release and vintage behavior |
| GDP/income/employment by region | BEA Regional API | FRED delivery where available | Selected | Frequency and publication lag vary |
| Multifamily supply pipeline | Census BPS | None | Proxy only | Residential permits, not completed CRE inventory |
| Rates and spreads | FRED/ALFRED or originating agency | Federal Reserve scenario history | Selected | Series-level rights, units, transformations, vintages |
| Scenario paths | Federal Reserve final scenario CSVs | Internally approved paths later | Benchmark only | No scenario weights inferred from publication |

## Required mapping record

Each implemented field mapping must record `mapping_id`, source ID, source
schema/tag and version, target field, formula, units, date rule, null rule,
valid-value rule, relationship cardinality, transformation version, test ID,
owner, status, and evidence location.

