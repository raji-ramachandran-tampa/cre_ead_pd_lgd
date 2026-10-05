# Signed source net-loss research fit

User accepted a signed, uncapped source net-loss ratio. Raw histories reconcile
584 old cases plus 88 restored gains to 672: training 632, validation 29, OOT 11.

| Candidate | Historical MAE | Validation MAE | OOT MAE |
|---|---:|---:|---:|
| Mean benchmark | 30.06 | 37.63 | 76.75 |
| Ridge with loss-sharing | 28.64 | 35.67 | 79.21 |

Units: loss-ratio percentage points. Four retrospective expanding backtests cover
615 evaluations. Loss-sharing ridge supports research comparison but does not
beat the mean OOT. No model selected. Source allocated gains are not borrower profits
or verified economic recoveries. Missing denominators remain excluded.

## Scope and evidence restrictions

Status: development research, not institutional approval or independent validation.
Detailed source case records, identifiers, financial amounts, locations and dates
are retained only in restricted external artifacts and local review documents.
This repository record contains aggregate evidence. Models are frozen and no
case exclusion or target change is approved by this document.

See `../prompts/CRE_PROJECT_RESTART_PROMPT_2026-10-05_LGD_BASELINE.md` for the
current verified handoff. The signed source net-loss ratio and synthetic economic
collateral calculations are separate outcomes; no economic expected-loss integration
or production use is established. Source revisions and availability remain open.
