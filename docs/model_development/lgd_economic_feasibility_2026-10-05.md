# Discounted economic LGD — source feasibility and calculation bridge

October 5, 2026. Model development; research only. Audience: developer and reviewers. The CPI ridge signed-loss baseline remains unchanged. No empirical economic-LGD labels or fitted economic model have been created. Owner, default definition and discount convention remain open.

## Calculation

At an agreed default date, economic LGD is:

`1 - [sum(recovery_i / (1+r)^t_i) - sum(cost_j / (1+r)^t_j)] / EAD_at_default`

Times are fractional years from default; this illustration uses annual effective compounding. Recoveries include verified collateral, borrower and guarantee/lender receipts. Costs are cash outflows attributable to workout. Preserve uncapped signed raw results. Rate convention must match intended use and cash-flow basis; neither CPI nor the predictive Treasury feature automatically defines that rate.

Do not discount the reported loss ratio itself, or infer all recoveries as EAD minus reported loss without an accounting reconciliation. Foregone interest is not automatically an additional cash expense; distinguish already-included interest from time-value discounting to avoid double counting. Institutional net loss and whole-loan economic loss are different perspectives when loss sharing exists.

## Source contract audit

The actual 2026Q1 Multifamily ZIP header has 62 fields. Loss-related fields include Default Amount, Lifetime Net Credit Loss Amount, Sale Price, Foreclosure Value, Foreclosure Date, Credit Event Date, Liquidation/Prepayment Date, Credit Event Type, Loss Sharing Type and Modified Loss Sharing Percentage. The inspected schema does not supply a complete dated ledger of recovery, expense, rental-income and reimbursement transactions.

The [official Multifamily glossary](https://capitalmarkets.fanniemae.com/media/5986/display) defines reported net loss as a composite of charge-offs, accrued foregone interest and net workout cash flows, offset by third-party loss sharing and insurance. The official credit event date is REO sale/disposition for REO cases, not necessarily default onset. Consequently event-to-report intervals and changes in reported cumulative loss are not proven recovery cash-flow dates or transactions.

| Required economic input | Current evidence | Remaining gap |
|---|---|---|
| Default date | Monthly delinquency history, event and foreclosure dates | Agreed PD-aligned onset/cure/episode rule |
| EAD at default | Default Amount and monthly balances | Principal/interest/advances basis and exact default-time reconciliation |
| Recovery amounts and dates | Partial sale price, event dates, aggregate net loss | Full cash ledger and receipt dates; gross property sale is not loan entitlement |
| Workout costs and property income | Embedded aggregate source outcome | Separate amounts, dates and scope |
| Lender/insurance benefits | Category and aggregate net offsets | Amounts, receipt dates and contractual basis; prevent duplicate offsets |
| Discount rate | Note-rate and market-rate information | Purpose-specific convention; fixed or term structure; rate-date basis |
| Resolution/finalization | Reporting snapshots | Residual future costs/recoveries and label-finalization evidence |

The existing collateral layer additionally requires complete security links and competing claims before allocating sale proceeds. Acquisition LTV is not a current realization valuation.

## Executed sensitivity example

Existing `discounted_workout_lgd` was used for twelve synthetic amount/timing/rate combinations. EAD 100, recovery 80, no costs or loss sharing; values below use an illustrative 5% annual effective rate. These are not observations or estimated discount rates.

| Recovery delay | Economic LGD |
|---|---:|
| Immediate | 20.00% |
| One year | 23.81% |
| Two years | 27.44% |
| Three years | 30.89% |

At zero rate all delays produce 20%; at 10%, two-year delay produces 33.88%. This illustrates why delayed recoveries raise loss relative to an otherwise identical nominal outcome. Real cost timing can change the result independently.

External immutable `lgd-economic-feasibility-v0.1.0/report.json` records the inspected raw header and synthetic examples; no loan rows are included. Calculator and collateral unit tests already form part of the complete suite (85 passed, five skipped). No new calculator implementation was needed.

## Next empirical step

Create a cash-flow input contract with loan/episode ID, default date, EAD basis, transaction ID, amount, currency, kind, actual date, source, perspective and inclusion flags. Reconcile undiscounted totals first, including loss-sharing treatment and foregone interest. Then compute discounted outcomes under explicit rate conventions and compare them with signed reported ratios. Fit an economic model only once actual labels are supportable. If only aggregate data remain available, any single-recovery timing bridge must be labeled a sensitivity proxy, not observed economic LGD.

Default mapping and discount-rate choice are open decisions; missing transaction histories cannot be repaired by assigning an arbitrary rate. No population exclusion, baseline replacement, EL integration or production approval follows from this feasibility work.
