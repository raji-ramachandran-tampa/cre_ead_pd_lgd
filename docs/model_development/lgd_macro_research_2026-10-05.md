# LGD macroeconomic challenger: October 5, 2026

Status: model-development research; no model selected, independently validated or approved.
Audience: model developers, owners and research reviewers. Population: Fannie Mae multifamily event loans.
Purpose: test literature-motivated macro increments while retaining signed-source-ratio-v0.1.0, frozen baselines and fixed regularization.

## Inputs and timing

- CPIAUCSL: national all-items seasonally adjusted CPI. Feature is six-month log change in decimal units. Assumed availability is observation-month start plus two months.
- COMREPUSQ159N: IMF national all-CRE **year-on-year percentage change**, not an index level. Divide by 100; do not calculate another growth rate. National all-CRE is a proxy for local multifamily collateral prices. Assumed availability is quarter start plus six months; repeat with nine months.
- New immutable public snapshots retrieved October 5, 2026, with source URLs and SHA256 hashes. Latest revised values, not historical vintages. Assumed lags do not establish actual publication availability.
- Backward-only joins use the existing pre-event feature_date. No future recovery-period observations enter features. That feature date is not an approved default-onset definition.
- Existing acquisition LTV, underwritten DSCR, log acquisition UPB, property type and loss-sharing category retained. Unemployment was not added.

Sources: [CPI](https://fred.stlouisfed.org/series/CPIAUCSL), [national CRE prices](https://fred.stlouisfed.org/series/COMREPUSQ159N).
Method motivation: [FDIC CRE study](https://archive.fdic.gov/view/fdic/11959/fdic_11959_DS1.pdf), [CPI CRE working paper](https://arxiv.org/html/2402.15498v1). The CPI paper floors losses at zero; this experiment preserves our signed outcome and does not replicate that target.

## Design and coverage

Full-population CPI experiment covers all 672 eligible loans and all four historical expanding folds (615 evaluation cases). Fixed later comparisons use training through 2018, validation 2019–2022 (29), examined OOT 2023 onward (11).

CRE series starts in 2005. Six-month lag covers 641 loans; nine-month lag covers 640. Missing early macro coverage removes 31/32 training loans only. Each covered-sample comparison refits both no-macro baselines and macro challengers on exactly the same population. The earliest 2008 training fold has only 15/14 loans and insufficient negative cases for the hurdle; all candidates in that comparison skip it. Remaining three folds evaluate 437 cases. These results cannot be compared directly with the 615-case full-population scores.

Candidates add CPI, CRE, or both to ridge and signed hurdle. Ridge alpha=10, logistic C=0.1, Gamma alpha=10 remain fixed. All scaling and component preprocessing fit within training samples. Zero probability is training frequency. No caps, floors, class weighting, tuning or calibration.

## Results

MAE in loss-ratio percentage points; lower is better.

| Full population candidate | Historical 615 | Validation 29 | Examined OOT 11 |
|---|---:|---:|---:|
| Ridge baseline | 28.640 | 35.671 | 79.214 |
| Ridge + CPI | 28.148 | 35.640 | 79.161 |
| Hurdle baseline | 29.520 | 37.313 | 76.726 |
| Hurdle + CPI | 29.366 | 37.322 | 76.771 |

Full-population baseline scores reproduce frozen metrics. CPI reduces historical ridge MAE by 0.492 points, about 1.72% relative; conditional paired 95% interval is [-0.777, -0.214] points. Hurdle reduction is 0.154 points, interval [-0.229, -0.079]. These 2,000 fixed-error MBS-group resamples exclude parameter estimation uncertainty and unknown borrower correlation; multiple exploratory comparisons were made.

| Covered sample historical 437 | CRE lag six months | CRE lag nine months |
|---|---:|---:|
| Ridge baseline | 26.641 | 26.705 |
| Ridge + CRE | 26.512 | 26.686 |
| Ridge + CPI + CRE | 26.527 | 26.697 |
| Hurdle baseline | 28.450 | 28.555 |
| Hurdle + CRE | 28.287 | 28.473 |
| Hurdle + CPI + CRE | 28.249 | 28.426 |

Property-price increments are small and timing-sensitive. CPI's full-population gain does not persist to the same extent in the shorter covered sample. Later results do not show a material repair of the unusual gain cases.

## Reproduction and artifacts

Run the installed project environment:

```powershell
python -m cre_expected_loss.models.lgd_macro_research --artifact-root <Fannie artifacts/2026Q1> --input-root <macro snapshot directory> --output <new immutable output directory>
```

Input directory contains CPIAUCSL.csv, COMREPUSQ159N.csv and manifest.json. Existing output raises FileExistsError. Authoritative external version: lgd-macro-research-v0.1.0; report.json contains aggregate metrics, coverage, fold counts, conditional sign/severity diagnostics, bootstrap comparisons, input hashes, runtime and limitations. predictions.parquet and models.joblib remain restricted external artifacts. Lag label 0 denotes full-population CPI-only scope, not zero publication lag. Lag labels 6/9 denote CRE-covered scopes.

## Interpretation and next work

Retain CPI as a promising research driver, not a selected model. Obtain historical publication/vintage evidence for CPI and CRE and a longer, more relevant multifamily/property-market series if available. Continue loan-history and source-gain reconciliation work. Do not infer causal macro effects from these associations or integrate the signed outputs automatically into bounded EL aggregation. Revised loan labels, unknown finalization dates, sparse recent outcomes and already-examined OOT prevent independent validation claims. Frozen baseline and prior target population remain unchanged.

Verification: synthetic tests cover growth units, assumed date alignment, rejection of post-event feature dates, signed predictions and training-only scaling. Complete repository test results are recorded after integration below.

Integrated verification: 78 passed, five existing Pandoc-dependent checks skipped. No production or model-selection decision.


Fold stability: the CPI ridge improvement is concentrated in the 2009-2011 evaluation fold (MAE 33.849 to 31.890). It slightly worsens 2012-2014 (24.776 to 24.883) and 2015-2018 (29.367 to 29.510), and barely improves 2019-2022 (35.671 to 35.640). Pooled bootstrap benefit is therefore not evidence of consistent improvement across periods.



## Subsequent baseline designation

On October 5, 2026 the user chose ridge + CPI as the working research baseline. See `lgd_cpi_baseline_2026-10-05.md` and external `lgd-cpi-baseline-v0.1.0`. This supersedes the earlier recommendation to keep CPI unselected; experiment results and original baseline artifacts are unchanged. Independent validation and a Git checkpoint remain pending.
