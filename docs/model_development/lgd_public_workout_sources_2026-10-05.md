# Public recovery and workout data search — October 5, 2026

Scope: dated recoveries and workout costs for CRE/multifamily economic LGD. Status: source discovery, not verified complete ledger or dataset integration. Current CPI signed-source baseline unchanged. No sign-in, registration, data license acceptance or external messaging performed. Public source pages and report schemas inspected; no loan records added to Git.

## Main finding

Public CRE disclosures contain useful liquidation amounts and timing, especially CMBS trustee investor reports. A complete downloadable transaction-by-transaction economic-workout ledger covering our existing Fannie loans was not established. This is a search result, not proof that no such dataset exists.

| Candidate | Verified contents and access | Fitness for next step |
|---|---|---|
| SEC EDGAR CMBS 10-D trustee exhibits | Public dated distribution reports; loan-level liquidation tables with proceeds, expenses, net proceeds, loss and adjustments | Strongest public CRE pilot; reconstruct longitudinal coverage and definitions before computing labels |
| Freddie Multifamily MSIA | Complimentary login tool with monthly standard investor reporting packages, according to official page | Strong multifamily lead; full cash-ledger completeness and access not verified |
| Freddie Multifamily MLPD | Public quarterly loan panel/snapshot; default/REO dates and credit-loss amount in dictionary | Useful duration/outcome comparator; dictionary does not expose full dated receipts and cost ledger |
| Freddie/Fannie single-family loan performance | Recovery and expense components; large datasets; registration/terms apply | Methodology demonstration only, a different population; transaction timing still requires assumptions/evidence |
| FDIC CRE loss-share studies | Public papers describe program-administration data used for economic loss research | Literature evidence; no public microdata download located in inspected research sources |

## Concrete CMBS evidence

Inspected [Citigroup Commercial Mortgage Trust 2018-C5 October 2025 trustee exhibit](https://www.sec.gov/Archives/edgar/data/1740450/000162829725000787/ex99_1.htm). The historical liquidation table contains beginning balance, proceeds received, liquidation expense, net proceeds, trust loss, adjustment fields and distribution date; unscheduled-principal tables also disclose liquidation/prepayment date. A populated historical row was present, demonstrating actual amounts rather than a blank template. That row's payoff code and zero trust loss do not establish an eligible default case. No individual values or identifiers copied into this repository.

Distribution date is a trust allocation date, not automatically the underlying expense or borrower receipt date. A loan liquidation table can combine expenses incurred over years. Beginning scheduled balance is not automatically EAD at default; realized loss to trust differs from whole-loan economic loss. Advances, accrued interest, fees, loan/property allocation and participation shares require documentation. Monthly/cumulative fields must be classified before differencing; corrections are not necessarily cash movements. Report layouts and coverage vary by deal. XML ABS-EE filings exist, but an attempted asset XML retrieval failed; its field coverage was not verified. Do not claim Schedule AL alone supplies a complete cash ledger.

Additional report discovery: [CSMC 2015-SA3 January 2026 exhibit](https://www.sec.gov/Archives/edgar/data/1647980/000188852426002011/csc15sa3_ex991-202601.htm) and [CSMC 2015-SA2 April 2026 exhibit](https://www.sec.gov/Archives/edgar/data/1639353/000188852426007416/csc15sa2_ex991-202604.htm) are search-index leads with historical liquidation tables. Full coverage/amount extraction was not performed, and the latter direct fetch failed. Prioritize stable public reports with resolved multifamily defaults, not arbitrary sample rows.

## Other primary sources

[Freddie Multifamily performance and tools](https://mf.freddiemac.com/investors/performance-lookup) describes MSIA as complimentary, providing monthly master-servicer/trustee investor reports; [MSIA guide](https://mf.freddiemac.com/docs/mulitfamily_securities_investor_access_user_guide.pdf) was opened. Tool login and dataset contents were not accessed. Public [SBL report](https://mf.freddiemac.com/docs/sbl_deal_performance_report.pdf) exposes special-servicer transfer amount/date, resolution date/type and loss amount. Transfer to servicing is not proven default onset.

[MLPD dictionary](https://mf.freddiemac.com/docs/MLPD_data_dictionary.pdf) inspected: quarterly observations and a credit-loss amount, with revisions and reporting scope limitations. It is not evidence of a complete workout receipt/cost ledger.

[Freddie single-family dataset](https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset) documents sales proceeds, insurance/other recoveries and expenses, with sign-in and research-use terms. Its [guide](https://www.freddiemac.com/fmac-resources/research/pdf/user_guide.pdf) says trailing expenses/recoveries can update the final disposition record later: therefore monthly reporting dates do not establish payment dates. This is useful for a separately labeled residential demonstration, not pooled CRE training.

[Fannie single-family source](https://capitalmarkets.fanniemae.com/credit-risk-transfer/fannie-mae-single-family-loan-performance-data) and [current field glossary](https://capitalmarkets.fanniemae.com/media/6931/display) disclose richer loss components than the multifamily source. Again this changes population, and aggregate expense/proceeds fields do not solve transaction timing automatically.

[FDIC CRE/commercial loan study](https://archive.fdic.gov/view/fdic/11956/fdic_11956_DS1.pdf) identifies its underlying source as the FDIC loss-share program administration database. Public paper availability is not microdata availability; no public downloadable loan ledger was located in this search. No confidentiality status or impossible-access claim is inferred.

## Recommendation

Pilot public CMBS trustee reports for a small set of resolved multifamily defaults, maintaining a separate population. Assemble a monthly report chain from before default through trailing adjustments, cross-check contract definitions, and map each field to observed cash, accounting total or timing proxy. Assess amounts, default-time EAD and ledger completeness first; do not promote the strict economic calculator's completeness flags without evidence. If full payment dates are absent, calculate explicitly labeled monthly or terminal-recovery sensitivity proxies alongside nominal reconciliation, rather than call them observed economic LGD. Existing Fannie loans cannot be assumed to match CMBS/Freddie records; a verified identifier/property/transaction crosswalk is required.

No source was downloaded into modeling inputs, no economic labels fitted and no baseline change. Next feasible action is the public CMBS coverage pilot; MSIA may be a complementary lead requiring login.
