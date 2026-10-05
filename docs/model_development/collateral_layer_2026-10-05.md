# Collateral recovery layer — implementation record

October 5, 2026. Lifecycle: model development. Status: proposed deterministic benchmark implementation with synthetic evidence, not calibrated or institutionally approved. Audience: developer/owner/research reviewers. User authorized implementation of collateral recovery and separate allocation interfaces. No empirical source-target change, refit or deployment.

## Implemented behavior

Module `src/cre_expected_loss/models/collateral.py` separates secured claims, documented property/security interests, timed property sales, recoveries and external loss allocation.

- Deduct explicit priority selling costs once from property proceeds.
- Pay claim ranks sequentially; equal-ranked claims receive proportional allocations based on their remaining claims.
- Maintain global remaining claim balances across properties, so shared security cannot recover more than a claim's specified amount.
- Record unused property surplus separately rather than assigning it as a loan gain.
- Reconcile each property's gross proceeds to selling costs, allocated recoveries and surplus.
- Convert allocated loan recoveries and separately supplied additional costs/benefits into dated cash flows for the existing uncapped discounted-workout-LGD function.
- Provide a generic positive nominal loss-sharing interface with explicit lender fraction and optional cap; amounts sum to the supplied loss basis.

The sharing interface is a **generic pro-rata contract**, not an implementation of Standard DUS, Pari Passu or Full Lender Loss based on the category name. Contractual loss basis, caps, exclusions and payment timing must be verified. Nominal sharing amounts are not automatically deducted from discounted economic losses. Any reimbursement entering economic LGD must have an explicit amount and date.

External benefits require unique source identifiers; already-net source-loss bases are rejected, preventing automatic reapplication to Fannie net outcomes. Reconciliation still requires checking that differently named insurance/guarantee benefits do not represent the same underlying recovery. Selling costs already deducted at property level must not appear again as separate loan costs; that semantic distinction remains a documented input contract.

## Worked synthetic example

All quantities and contract terms below are invented for testing, not estimates for Fannie loans.

| Item | Illustrative monetary units |
|---|---:|
| Gross property sale proceeds | 100 |
| Priority selling costs | 10 |
| Net available proceeds | 90 |
| Senior claim / recovery | 80 / 80 |
| Junior claim / recovery | 50 / 10 |
| Unrecovered junior nominal claim | 40 |

At a one-year recovery time and 10% discount rate, junior economic LGD is `1 - (10/1.1)/50 = 81.82%`. Under a separate hypothetical 50% lender participation capped at 15, the nominal 40 loss divides into lender 15 and institution 25. If a verified reimbursement of 15 is paid at year one, economic LGD becomes `1 - ((10+15)/1.1)/50 = 54.55%`. This differs from nominal 25/50 because recoveries are delayed. The hypothetical participation contract is not asserted to be a Fannie contract.

Synthetic example output is saved in the working workspace as COLLATERAL_SYNTHETIC_EXAMPLE.json. Tests separately verify equal-rank allocation and two-property global claim limits.

## Required real-data contract

| Input | Current Fannie evidence | Readiness |
|---|---|---|
| Loan/claim amount at modeled default | Source default amount available on selected cases | Default onset and principal/interest basis need reconciliation |
| Property/pool IDs and linked loans | Property counts and geography | Complete security links unavailable; location alone insufficient |
| All senior and equal-ranking claims | Own-loan lien position | Competing lien balances and complete stack missing |
| Realizable collateral value at prediction date | Acquisition LTV; later event valuations | No verified current point-in-time valuation/scenario path |
| Sale price and realization timing | Partial post-event source fields | Eight of eleven OOT sale prices missing |
| Priority selling costs / other workout costs | Embedded in reported net loss | Separate amount and timing unavailable |
| Insurance/guarantee/lender reimbursements | Embedded source offsets | Individual benefits and payment dates unavailable |
| Contract loss-sharing formulas and basis | Category labels | Full verified mapping absent, including unusual category |
| Scenario-specific valuations and costs | No fitted collateral transmission | Proposed, not assumed |

No real-data waterfall was run. Acquisition UPB/LTV was not substituted for a verified current property appraisal, especially for supplemental loans/facilities. Fannie reported signed net-loss ratios were not fed into this economic calculation.

## Limits of the deterministic interface

Each property is represented by one realization. Claims share a common default-time origin and explicit current recovery entitlement; claim accrual during workout is not inferred. Costs specified as priority selling costs are assumed to legally precede secured claims; other competing claims must be included explicitly at their correct rank.

Sales are processed by realization time, then a supplied unique allocation order. Simultaneous cross-collateral allocations can depend on that ordering; it is a documented contractual input, not an optimized or universally order-invariant solution. More complex marshaling, per-property security limits, tranche caps, revolving claims, additional sales and changing claim balances require extensions. No legal enforceability or underlying security documents were verified.

Collateral recoveries are capped at specified claims, but raw economic LGD is not automatically capped/floored. Separately justified external benefits can yield negative raw economic LGD. Whether bounds are appropriate for projected expected loss is an open policy/target decision. Existing expected-loss aggregation requires projected LGD in [0,1]; this research layer is not automatically connected to it.

## Tests and change record

Full suite: **75 passed, five Pandoc checks skipped**. New tests verify senior priority, equal-rank allocation, property reconciliation, cross-property claim limits, discounting, separate benefit/cost recombination, uncapped raw LGD, nominal contract caps, duplicate benefit IDs, rejection of already-net bases, invalid values, unknown claims, duplicate links/properties/orders and costs exceeding proceeds.

Changed files: new collateral module, `tests/test_collateral.py`, this implementation record. Existing statistical models, target, datasets and empirical outputs preserved. No commits or pushes. Rollback is to stop using the new standalone interface; prior modules remain usable. Material future data/scenario/contract integrations require fresh tests, reconciliation and methodology review.

Next usable increment requires a controlled input package with collateral linkage, complete claims, valuation dates and supported contract/recovery cash flows. Until available, this is a tested synthetic benchmark layer alongside the empirical signed-source model, not a claim of fitted collateral LGD.
