# Signed LGD interest-rate and credit-spread research — October 5, 2026

Status: exploratory model development; no candidate selected. Audience: developers and reviewers. Intended use: evaluate macro drivers of the signed source-reported net-loss ratio. This is not discounted economic LGD or independent validation. Owner/approval: TBD. Frozen research baseline remains unchanged.

## Hypotheses and sources

Collateral prices, inflation, financing conditions and broad credit stress can affect recoveries and workout losses. The [FDIC CRE loss study](https://archive.fdic.gov/view/fdic/11959/fdic_11959_DS1.pdf) motivates collateral and loan characteristics; the [Wu, Arora and Mei working paper](https://arxiv.org/html/2402.15498v1) motivates macro-conditioned severity, including six-month inflation and property-price changes. Neither establishes that our particular Treasury/spread specification improves this signed target. Their populations and outcome treatment differ.

This experiment adds [DGS10](https://fred.stlouisfed.org/series/DGS10), the daily 10-year Treasury yield, and [BAA10YM](https://fred.stlouisfed.org/series/BAA10YM), the monthly Baa corporate yield less the 10-year Treasury yield. Baa spread is a broad corporate credit proxy, not an observed CRE lending spread. No unemployment feature was added.

## Specification and reproducibility

Implementation: `src/cre_expected_loss/models/lgd_rates_research.py`; tests: `tests/test_lgd_rates_research.py`. CLI requires explicit artifact-root, macro-root, rate-root and output paths. Reuse the preceding signed outcomes and macro experiment inputs. Output version `lgd-rates-research-v0.1.0` is immutable and outside Git under the external 2026Q1 artifact root. It contains report.json, restricted predictions.parquet, models.joblib and ridge_coefficients.csv. The report records source SHA-256 hashes, macro manifest, coverage, metrics, folds, conditional paired intervals and hurdle component diagnostics. Loan records, raw inputs and model binaries are not repository additions.

DGS10 is averaged by observation month and divided by 100; BAA10YM is divided by 100. Six-month Treasury change is the difference in decimal yields, not a relative percentage change. Monthly reference dates use the month start. Availability is assumed two months later, with a three-month sensitivity. Backward joins prohibit dates after the existing feature date. CPI remains six-month log change with a two-month assumed lag; CRE remains the already-reported annual price change, divided by 100, with six/nine-month assumed lags.

Rate inputs use the existing September 16, 2026 revised FRED snapshot; CPI/CRE inputs were retrieved October 5. These mixed snapshot dates are explicit, not historical vintages. Publication lags are assumptions, not observed release dates. Loan feature dates precede disposition but may be during workout; monthly reporting dates also do not establish public availability.

Models reuse training-only preprocessing and fixed regularization: ridge alpha 10; hurdle sign logistic C 0.1, Gamma magnitude alpha 10 and training zero frequency. Signed gains are preserved and modeled by their separate magnitude branch. No flooring, capping, class reweighting, outcome exclusions, tuning or OOT calibration was introduced.

Full-sample candidates: baseline, CPI, Treasury level, spread level, six-month Treasury change, Treasury plus spread, and CPI plus Treasury/spread. CRE-covered comparisons additionally include CPI+CRE and CPI+CRE+Treasury/spread. Each is evaluated with ridge and signed hurdle models, alongside a training mean benchmark.

The full scope covers all 672 outcomes and 615 historical evaluations across four chronological folds. Later comparisons are 29 validation and 11 already-examined OOT cases, trained on outcomes through 2018. Historical folds purge overlapping MBS transaction groups. CRE coverage is 641 at the primary lag, 640 at longer lags; exclusions are early training observations. The earliest CRE fold is skipped for every candidate because training sign branches are sparse, leaving 437 matched historical evaluations. Comparisons across those scopes cannot be interpreted as feature gains.

## Results

MAE in percentage points; lower is better. Full-sample ridge:

| Candidate | Historical, 615 | Validation, 29 | OOT comparison, 11 |
|---|---:|---:|---:|
| Baseline | 28.640 | 35.671 | 79.214 |
| CPI | 28.148 | 35.640 | 79.161 |
| Treasury level | 33.178 | 35.608 | 79.423 |
| Credit spread | 28.537 | 34.801 | 78.500 |
| Treasury change | 28.573 | 35.295 | 79.616 |
| Treasury + spread | 31.871 | 34.342 | 79.730 |
| CPI + Treasury + spread | 31.524 | 34.534 | 79.445 |

Adding Treasury/spread to CPI raises historical ridge MAE by 3.376 points. Its conditional 95% paired interval is +2.615 to +4.109 points. Spread alone improves the baseline by only 0.103 points and trails CPI by 0.389 points. The apparently better validation/OOT spread scores do not establish a robust overall improvement or justify selecting on those small, examined periods.

Full-sample hurdle historical MAE is 29.520 baseline, 29.366 CPI, 29.355 spread and 29.874 CPI+Treasury/spread. Spread is only 0.011 points better than CPI historically; no material evidence of superiority follows from that difference.

On the primary CRE-covered sample, hurdle CPI+CRE+Treasury/spread improves historical MAE from 28.249 to 28.150, and validation from 37.124 to 36.114, but OOT worsens from 77.250 to 80.137. The longer-lag historical hurdle increment is similarly small (28.426 to 28.316), with worse OOT (77.298 to 79.586). Ridge combined CRE/rates worsens historical MAE at both lags. These are mixed findings, not a selected specification.

Paired intervals use 2,000 fixed-prediction MBS-group bootstrap samples, seed 20260901. They exclude fitting uncertainty, unknown borrower grouping and multiple-comparison adjustment; they are exploratory uncertainty summaries.

## Verification and decision

85 pytest tests passed; five Pandoc-dependent checks skipped. Existing history test emits one pandas deprecation warning. New tests verify monthly averaging, decimal units, six-month differences, timing sensitivity, missing prehistory and duplicate rejection. New code lint passes. Full baseline/CPI predictions reconcile to the preceding macro artifact for 655 historical/later predictions per candidate at absolute tolerance 1e-8; ridge discrepancies are below 1e-12, hurdle optimizer differences are negligible. Reloaded ridge/hurdle combined models reproduce the 29 validation predictions within 1e-8.

Recommendation: retain the frozen baseline; keep CPI and CRE as research candidates. Adding these rate/spread proxies does not establish a better overall model. Better evidence requires dated macro/loan vintages, local multifamily collateral measures, and independent future outcomes. Literature provides hypotheses and mechanisms, not a guarantee of better accuracy in this small, heterogeneous signed-loss sample. No model selection, baseline replacement, EL integration, regulatory claim or production approval occurred.

Change classification: additive research module and aggregate evidence. Rollback requires no baseline restoration: the baseline and raw inputs were untouched. Repository changes are uncommitted pending a separately requested check-in.


## Subsequent baseline designation

On October 5, 2026 the user chose ridge + CPI as the working research baseline. See `lgd_cpi_baseline_2026-10-05.md` and external `lgd-cpi-baseline-v0.1.0`. This supersedes the earlier recommendation to keep CPI unselected; experiment results and original baseline artifacts are unchanged. Independent validation and a Git checkpoint remain pending.
