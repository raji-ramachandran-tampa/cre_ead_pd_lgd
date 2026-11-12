# Manuscript claim register

Updated November 12, 2026. EAD Tables 1 and 2 are now regenerated directly from
frozen aggregate reports with input SHA256 hashes in ../tables/ead_table_provenance.json.
Other figures remain transcribed from the linked development records. This checks
transcription and version/population consistency,not independent model reproduction.
Before final submission,verify every table and PD/LGD claim against final artifacts.

| ID | Claim | Source relative to this file | Qualifications/status |
|---|---|---|---|
| D1 | 5,392,800 monthly rows;73,048 loans;4 identical EAD-projection duplicates | [Audit](../../docs/model_development/ead_source_audit_2026-10-06.md) | Original rows vs selected-column dedup distinguish |
| L1 | Signed LGD672,88 negative,13 zero;632/29/11 cohorts | [LGD restart](../../docs/prompts/CRE_PROJECT_RESTART_PROMPT_2026-10-05_LGD_BASELINE.md) | Disposition-year; signed source ratio, not economicLGD |
| L2 | CPI ridge MAE28.148/35.640/79.161pp | [CPI baseline](../../docs/model_development/lgd_cpi_baseline_2026-10-05.md) | Historical615,validation29,examinedOOT11; revised macro |
| E1 | EAD nonlinear/schedule/ridge matched table | [Advanced results](../../docs/model_development/ead_advanced_results_2026-11-02.md) | Supported fixed/unmodified/pre-maturity; not full routed cohort |
| E2 | NonIO90% interval coverage85.63%/89.08% recent3/12months | [Advanced results](../../docs/model_development/ead_advanced_results_2026-11-02.md) | Different mean/quantile cutoffs; no coverage guarantee |
| E3 | Prior-payment reconstruction111/115 accepted;recent6/4;full-population errors0.10836%/0.54087% | [Payment-history results](../../docs/model_development/ead_payment_history_2026-11-12.md) | Full eligible cohorts418/454;do not mix with supported advanced samples226/250 |
| E4 | Recent12m needed correction0.06801%,nonlinear0.28106% | [Payment-history diagnosis](../../docs/model_development/ead_payment_history_2026-11-12.md) | Net aggregate correction/observed principal;descriptive not causal |
| T1 | 2416 spells,2120 loans,238 multi-spell;660/66LGD linkage | [Episodes](../../docs/model_development/ead_observed_episodes_2026-10-06.md) | Observed status changes not contractual cure/default |
| T2 | Last-spell closer49/66;participation exact32/63;8of11 earlier onset | [Alignment](../../docs/model_development/ead_pd_timing_proposal_2026-10-06.md) | Hindsight diagnostic; no true-default selection |
| P1 | PD empirical results | Prior PD reports/external manifests | OPEN: audit population,features,event definition,metrics before insertion |
| A1 | AI-assisted workflow documented | Git history,project prompts,tests | No comparative productivity or causal quality evidence |
| I1 | Complete integrated economicEL | None | NOT ESTABLISHED; do not claim |

Source authority: glossary defines terms; empirical reports support project values;
papers support methodological context. Development evidence is not independent
validation. Tests124passed/five skips describe modeling verification atfcbf2b5,
not evidence that models are statistically validated or submission ready.
