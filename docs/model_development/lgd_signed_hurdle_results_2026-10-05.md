# Signed hurdle research challenger

Training: 547 positive, 72 negative, 13 zero cases. Constant zero probability
2.057%; regularized conditional sign logistic model; separate positive and
absolute-negative Gamma severity components. No oversampling or output cap.

| Candidate | Historical MAE | Validation MAE | OOT MAE |
|---|---:|---:|---:|
| Mean benchmark | 30.06 | 37.63 | 76.75 |
| Ridge with loss-sharing | 28.64 | 35.67 | 79.21 |
| Signed hurdle | 29.52 | 37.31 | 76.73 |

Units: loss-ratio percentage points. OOT sign frequency is overpredicted and gain
magnitude understated; eleven OOT cases cannot support independent selection.
Authoritative hurdle artifact is v0.1.1, with portable component serialization;
v0.1.0 is superseded. Tests verify probability sums, signed recombination,
uncapped magnitudes and saved-component reproduction.

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
