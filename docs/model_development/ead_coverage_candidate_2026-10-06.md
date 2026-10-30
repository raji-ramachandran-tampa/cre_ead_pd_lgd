# EAD interest-only guard and coverage candidate — October 6, 2026

Lifecycle: research development. User authorized continuation. Status: implemented
and evaluated candidate, no baseline designation, independent validation or EL
integration. Institutional owner TBD. Source and target definitions unchanged.
Code: scripts/ead_coverage_candidate.py; input ead-source-audit-v0.2.0 and frozen
ead-research-v0.1.2. Final external artifact ead-coverage-candidate-v0.1.1 contains
report.json/predictions.parquet; hashes source/model reports. v0.1.0 routing labels
superseded by stricter IO scope; hold values and aggregate results unchanged.

## Explicit routing

Fixed, no documented modification, before known maturity, IO end at/after horizon:
hold positive anchor principal. Assumes fully funded exposure, no new draw,
capitalization or term changes; does not verify actual funding or contract.
Otherwise use post-IO clock sensitivity where schedule supported. All remaining
initially eligible cases use balance hold with explicit unpaid-maturity or
unverified-schedule flag. No substitution of missing contract fields with zero.
Coverage is availability of a proxy estimate, not verified contractual coverage.

Routes for3months/12months: IOhold257/265; schedule956/970; unpaidmaturity206/207;
unverifiedschedulehold496/510. Eligible totals1,915/1,952. Horizons overlap.
Same principal target, no credit facilities, no accrued-interest/advance additions.
Current-status requirement and positive outcome requirement remain audit scope.

## Matched full-eligible comparisons

Error = SUM absolute dollars / SUM observed scheduled principal.

| Horizon | Onset period | Cases | Hold error | Routed candidate error |
|---|---|---:|---:|---:|
| 3 months | Through2018 | 1,002 | 0.3015% | 0.1667% |
| 3 months | 2019–2022 | 495 | 0.3479% | 0.1537% |
| 3 months | 2023 onward | 418 | 0.2647% | 0.1109% |
| 12 months | Through2018 | 1,018 | 1.2216% | 0.7433% |
| 12 months | 2019–2022 | 480 | 1.3633% | 0.6691% |
| 12 months | 2023 onward | 454 | 1.0594% | 0.5462% |

On matched supported ridge cases, applying the same structural IO hold guard
reduces recent error3months0.0908%to0.0516%(226),12months0.3697%to0.2445%(250).
This is a guard on frozen predictions, no new fitting or tuning. Recent guarded
ridge mean bias rises from0.0746%to0.1119% at12months despite lower absolute error;
no blanket calibration improvement claim. It remains worse than post-IO schedule
recent twelve-month supported error0.1937%, but represents a useful challenger.
Do not compare full-eligible0.5462% with supported-only0.1937% as equal populations.

## Verification and limitations

Executed run checks unique loan/horizon, finite nonnegative exposure and maturity
hold equality; raw/frozen data not altered. Lint passes. Prior full suite110passed,
five Pandoc skips; no new fitting or core calculation changes in this step.
No testing claim for contract truth: rules remain research assumptions.
Later observations have been examined and routing designed after segment review;
these improvements are development feedback, not independent confirmation.
Post-IO convention still unverified against loan documents, retained as sensitivity.
Unknown schedule, balloon, modification and funding behavior remain unresolved.
Maturity hold retains unpaid principal and does not predict payoff/refinancing.
No LGD denominator change or PD date change; aggregate expected loss not computed.

Recommendation: use the routed schedule candidate as the next research comparison
reference, retain guarded ridge challenger, and keep all route-quality flags.
Formal baseline selection/approval not inferred. Next: evaluate chronological
route backtests and errors on actual participation Delinquency UPB; quantify
principal/accrual/default-date differences on matched LGD loans. Keep principal
and broader exposure definitions distinct before EL integration.
Rollback preserves original EAD module and frozen artifacts. Local uncommitted.
