# Public CMBS workout pilot — initial coverage audit

October 5, 2026. Research source assessment, not empirical economic-LGD model development completion. User authorized pilot. Existing CPI/Fannie baseline unchanged. Only aggregate evidence in repository; case identifiers, amounts and detailed provenance remain external.

## Executed work and findings

Screened public trustee exhibits, including CGCMT 2013-GCJ11 (March 2017), CGCMT 2018-C5 (October 2025), CSMC 2015-SA3 (January 2026), JPMBB 2015-C33 (October 2025), and WFCM 2015-SG1 leads. These are purposive source checks, not a population sample. No uniform automated eligibility count across all reports is claimed.

CGCMT 2013-GCJ11 reports no historical liquidations. The earlier CGCMT 2018-C5 populated example was a zero-trust-loss payoff and does not establish default eligibility. JPMBB exhibits contain numerous resolved multifamily payoffs; special-servicing transfer alone is not an agreed default rule. No zero-loss case was excluded merely because loss was zero. Full default evidence and cash scope determine readiness.

One resolved multifamily foreclosure candidate was identified in WFCM 2015-SG1. Primary-source indexed servicing evidence supplies multifamily classification and an actual foreclosure narrative; a fully retrieved later trustee report supplies historical liquidation amounts and post-liquidation loss adjustments. This is stronger evidence than a template-only source, but not a complete dated workout ledger. Monthly chain coverage from pre-default through finalization remains incomplete.

## Reconciliation performed

Decimal arithmetic on the candidate's disclosed amounts gives:

- Proceeds less combined fees/advances/expenses equals net distribution proceeds exactly.
- Initial reported loss less cumulative adjustment equals adjusted reported loss exactly.
- Beginning scheduled balance less net distribution proceeds differs from initial reported loss by five cents. Retain the discrepancy; do not assert cent-exact full reconciliation or force a correction.

The report defines combined deductions to include P&I advances and unpaid fees. They cannot all be treated as independent economic workout costs. Post-liquidation adjustment rows demonstrate that the initial liquidation loss can change later; adjustment date is not proof of actual recovery receipt. Beginning scheduled balance is not verified default-time EAD. Distribution timing is not necessarily borrower receipt or expense-payment timing. The reported percentage loss uses original loan balance and should not be relabeled default-EAD LGD.

## Access and provenance

The [April 2026 WFCM trustee report](https://www.sec.gov/Archives/edgar/data/1648858/000188852426007976/wfc15sg1_ex991-202604.htm) was retrieved fully through web research and inspected for liquidation/adjustment tables and the combined-deduction note. [June 2022 servicing evidence](https://www.sec.gov/Archives/edgar/data/1648858/000188852422008025/wfc15sg1_ex991-202206.htm) was available through indexed primary-source excerpts; full retrieval failed. Evidence maturity is explicitly different for those sources.

Direct local SEC report retrieval returned HTTP403. No raw report bytes were downloaded, no checksum of a raw report is claimed, and no alternate identity or access-control workaround was attempted. Several other web report fetches also failed. Restricted external `cmbs-workout-pilot-v0.1.0` stores `case_evidence.json` and `manifest.json` under the separate CMBS artifact root: linked sources, manual transcription status, dates, raw fact values, computed residuals and gaps. It is not a parser-generated or complete cash-flow dataset.

## Current readiness and next increment

One resolved multifamily foreclosure candidate; zero complete economic ledgers; no fitted economic outcomes. Required next evidence: full pre-default-to-adjustment monthly sequence, PD-aligned default date, reconciled default EAD, actual cash dates, expense/advance/fee decomposition, adjustment nature, and finalization evidence. Do not populate `ledger_complete=True` or `observed=True` for inferred payments in the economic ledger interface.

If exact dates remain unavailable, terminal-recovery or monthly timing calculations must be separate sensitivity proxies with explicit assumptions. A full history with ambiguous cost basis still does not establish observed economic LGD. No Fannie/CMBS crosswalk, pooling, prediction refit, baseline replacement or EL integration was performed. Pilot is at initial coverage/accounting stage; source completeness remains open. No new production code required tests; two exact accounting identities and the unresolved residual were calculated directly.
