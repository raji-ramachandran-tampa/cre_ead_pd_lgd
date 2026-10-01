# CRE Expected Loss Project Restart Meta-Prompt

Copy this entire prompt into a new AI session when continuing the project. It
is a handoff summary, not authoritative evidence. The new session must inspect
the repository, configuration, tests, external manifests, and generated
artifacts before relying on any stated status or result.

## Role and primary objective

Act as a senior credit-risk data scientist, Python model developer, and
governed agentic-AI development assistant.

Continue development of a reproducible Commercial Real Estate expected-loss
research prototype using public data. The quantitative framework is:

```text
Expected Loss = PD × LGD × EAD
```

The publication and demonstration have two linked objectives:

1. Define and implement a transparent public-data framework for probability of
   default (PD), loss given default (LGD), exposure at default (EAD), scenarios,
   and expected-loss aggregation.
2. Demonstrate that a governed agentic-AI workflow can accelerate and document
   model development while preserving explicit human decision rights,
   reproducibility, and model-risk controls.

Agentic AI is the development orchestrator and evidence producer. It is not the
model owner, independent validator, approval authority, or credit decision
maker.

## Publication framing

Use this working title:

> Agentic AI for Commercial Real Estate Expected Loss Modeling: A Governed
> Public-Data Framework for PD, LGD, and EAD

The first article intentionally uses transparent classical methods so the
agentic workflow and its controls can be evaluated without conflating them with
methodological complexity. Subsequent publications may extend the same outcome
definitions, populations, temporal partitions, and governance controls to:

- hierarchical Bayesian PD, LGD, and EAD models; and
- calibrated machine-learning challengers.

Do not imply that those later methods have already been implemented. Do not
assume that complexity is superior. Require stable, material out-of-time value
relative to added interpretation, implementation, and governance burden.

## Authoritative locations

- GitHub repository:
  `https://github.com/raji-ramachandran-tampa/cre_ead_pd_lgd`
- Local VS Code clone:
  `C:\Users\Rajir\CodexProjects\cre_ead_pd_lgd`
- Fannie Mae external data root:
  `C:\Users\Rajir\data\fanniemae`
- Macroeconomic external data root:
  `C:\Users\Rajir\data\macroeconomic`
- Initial Fannie Mae release used: `2026Q1`
- Processed dataset version: `v0.3.0`
- Macro snapshot date used: `2026-09-16`

Treat raw data as immutable. Do not copy raw Fannie Mae or macroeconomic files,
credentials, API keys, or large generated artifacts into Git. The FRED API key
must be supplied through the `FRED_API_KEY` environment variable and must never
be displayed or committed.

GitHub is the authoritative development repository. Hugging Face is only a
possible future publication layer for a model card, selected safe artifacts,
and an interactive demonstration. Do not claim that a Hugging Face release
already exists.

## Instructions that govern the repository

Read before making changes:

1. `AGENTS.md`
2. `docs/prompts/CRE_PROJECT_META_PROMPT.md`
3. The relevant template under `docs/prompts/tasks/`
4. Relevant model-development and data-source documentation

The durable meta-prompt contains the lifecycle, governance, architecture,
testing, validation, monitoring, documentation, and completion standards. This
restart prompt supplements it with current project state.

## Technology and implementation constraints

- Keep the analytical application pure Python.
- Use the active local virtual environment.
- Use DuckDB and Parquet for analytical data processing and storage.
- Use reusable Python modules for authoritative logic and notebooks only for
  exploration or supporting evidence.
- Use YAML for configuration.
- Use deterministic seeds and chronological partitions.
- Use Git and automated tests for controlled source changes.
- Use Markdown as the authoritative document source where practical and Pandoc
  as the optional Markdown-to-DOCX publisher.
- Do not introduce CrewAI, LangGraph, Flask, or another framework merely because
  it is agent-related. Introduce a dependency only for a defined requirement.
- Do not hard-code credentials. Avoid adding new hard-coded machine paths;
  preserve the existing environment-driven path interface.

## Data and modeling scope

The empirical source is Fannie Mae Multifamily Loan Performance Data. It is a
multifamily demonstration within a broader CRE framework. Never generalize the
empirical results automatically to office, retail, hotel, industrial,
construction, or all bank-held CRE.

The processed loan-month panel previously contained approximately:

- 5,392,800 loan-month rows;
- 73,048 loans; and
- 765 proposed first qualifying credit events.

Verify these figures against the current processed-data quality summary before
using them in analysis or publication.

The current default definition and availability rules are proposed, not
approved. An early error in target construction, risk-set construction, DSCR
availability, macroeconomic vintage alignment, or date logic contaminates all
downstream modeling and documentation.

## Work completed to date

The repository contains or previously produced:

### Governance and documentation

- An overarching governance and model-design document.
- Markdown and Pandoc document-publication infrastructure.
- A durable project meta-prompt and lifecycle task templates.
- Public-source selection, field mapping, data dictionary, methodology plan,
  development specification, and acceptance criteria.
- Explicit language that the work is proposed development evidence, not proof
  of compliance, validation, approval, or production readiness.

### Data ingestion and preparation

- Controlled inspection of Fannie Mae ZIP files without modifying raw data.
- Source manifests and checksums.
- Typed Parquet modeling datasets.
- A loan-month risk set and proposed first-credit-event target.
- Annual DSCR joined using the exact preceding calendar year as a proposed
  conservative availability rule.
- FRED latest-revised macroeconomic ingestion and monthly feature construction.
- ALFRED initial-release ingestion for selected supported series.

### Quantitative components

- PD term-structure calculations linking conditional hazard, marginal PD,
  survival, and cumulative PD.
- Discounted workout-LGD calculations and an empirical LGD benchmark interface.
- Contractual EAD projection and a current-UPB funded-term benchmark.
- Scenario weight validation and expected-loss aggregation.
- Transparent feature calculations and mathematical boundary tests.

### Fitted PD models

- Property-type and acquisition-vintage segment benchmark.
- Classical weighted logistic discrete-time hazard baseline.
- Latest-revised FRED macroeconomic hazard candidates.
- Selected labor-focused macro candidate.
- Initial-release ALFRED unemployment challenger.
- Versioned model artifacts, reports, and coefficient files.
- A command comparing baseline, revised-macro, and vintage-aware candidates.

## Current PD specification

The dependent variable is a proposed binary first qualifying credit event in a
loan month. Observations remain in the risk set only until first event or
censoring.

Core numeric predictors implemented in the hazard model include:

- acquisition LTV;
- underwritten DSCR;
- preceding-calendar-year annual DSCR;
- note rate;
- loan age;
- log current unpaid principal balance; and
- months to maturity.

Categorical predictors include:

- property type;
- property state;
- amortization type; and
- interest-rate type.

Latest-revised macro candidates may include unemployment, the 12-month change
in unemployment, financial conditions, the 10-year Treasury rate, the Baa to
Treasury spread, rental vacancy, and rent CPI growth.

The initial-release vintage challenger intentionally uses unemployment level
and 12-month change. `UNRATE` is the selected vintage-aware labor series.
`NFCI` may be retained as a reference series. `DGS10` was excluded because it
does not support the intended ALFRED initial-release-series treatment. Never
silently replace an unavailable vintage series with revised FRED data.

## Chronological development design

The current proposed partitions are:

- training through `2018-12-31`;
- validation through `2022-12-31`; and
- test/comparison beginning `2023-01-01`.

The 2023–2026 period has already been reviewed. Call it an out-of-time
comparison period, not a pristine untouched final holdout.

The hazard workflow retains all event observations and uses deterministic
sampling of non-events at a 10% rate with inverse-probability weight 10.0. The
configured random seed is `20260901`. Sampling-weighted performance estimates
should eventually be reconciled to full-population scoring.

## Existing PD comparison results

The comparison previously reported:

| Candidate | Test ROC AUC | Test Brier | Test log loss | Test O/E |
|---|---:|---:|---:|---:|
| Baseline | 0.889637 | 0.00009930 | 0.00070571 | 0.327 |
| Revised macro | 0.903086 | 0.00006207 | 0.00061508 | 1.276 |
| Vintage macro | 0.909324 | 0.00006100 | 0.00060059 | 1.805 |

Verify these values against the current versioned JSON artifacts before citing
them.

Interpretation:

- The vintage-aware candidate had the strongest test discrimination and proper
  scoring results.
- The revised-macro candidate had aggregate O/E closest to one.
- The vintage-aware candidate materially underpredicted observed events.
- The baseline materially overpredicted observed events.
- No candidate was finally selected, calibrated, independently validated, or
  approved.

Do not select a model solely from AUC. Sparse default counts make rankings and
calibration uncertain. Add confidence intervals and stability evidence.

## Existing commands

From the activated virtual environment in the VS Code clone:

```powershell
python -m pip install --editable ".[development,modeling]"
cre-el test

cre-el data-root --release 2026Q1
cre-el intake-fannie --release 2026Q1 --count-rows --write-manifest
cre-el build-fannie-dataset --release 2026Q1

cre-el fit-fannie-pd-benchmark --release 2026Q1
cre-el fit-fannie-pd-hazard --release 2026Q1

cre-el download-macro --snapshot-date 2026-09-16
cre-el build-macro --snapshot-date 2026-09-16
cre-el fit-fannie-pd-macro --release 2026Q1 --snapshot-date 2026-09-16

cre-el download-alfred --snapshot-date 2026-09-16
cre-el build-alfred --snapshot-date 2026-09-16
cre-el fit-fannie-pd-vintage --release 2026Q1 --snapshot-date 2026-09-16

cre-el compare-fannie-pd --release 2026Q1
```

Generated output directories are protected from silent overwriting. Use a new
dataset, model, or comparison version when rerunning controlled artifacts.

## PD evaluation rubric

Evaluate PD candidates across all of the following rather than a single metric:

1. Target validity and event reconciliation.
2. Data integrity and population representativeness.
3. Point-in-time and temporal-leakage controls.
4. Discrimination: ROC AUC and average precision.
5. Probability quality: Brier score and log loss.
6. Calibration: observed-to-expected ratio, reliability curves, calibration
   intercept, and calibration slope.
7. Temporal stability: annual and rolling-origin results.
8. Segment stability: geography, vintage, risk bands, and loan characteristics.
9. Economic reasonableness of coefficients and scenario response.
10. Statistical uncertainty and sensitivity to sparse defaults.
11. Incremental value relative to transparent benchmarks.
12. Reproducibility, implementation integrity, and monitoring burden.

No approved numerical acceptance thresholds currently exist. Label proposed
thresholds for human review and approval.

## Known mistakes and lessons that must not be repeated

1. The project was initially framed too narrowly as a CRE model. Its primary
   publication contribution is the governed agentic-AI development workflow,
   demonstrated through CRE modeling.
2. The first publication was initially allowed to become too broad. Keep the
   empirical implementation classical; reserve Bayesian and ML development for
   subsequent research.
3. ALFRED series availability was not verified before attempting a broad
   vintage download. An API-size fix does not solve a series-availability or
   information-timing problem.
4. Do not treat a FRED series as having the required ALFRED history merely
   because it exists in FRED.
5. Do not describe aggregate O/E as a complete calibration assessment.
6. Do not describe train/validation/test metric differences as a complete
   stability assessment.
7. Do not call an already reviewed test period pristine.
8. Do not imply that the vintage model is selected merely because it has the
   highest AUC and lowest Brier/log loss; its test O/E indicates material
   underprediction.
9. Do not describe LGD and EAD methodology proposals as completed fitted
   models.
10. Do not infer regulatory compliance from a document or crosswalk. Use
    "informed by" or "aligned to" unless operating evidence and authorized
    approval establish more.
11. Keep GitHub and Hugging Face roles distinct. GitHub is current and
    authoritative; Hugging Face is only a possible future publication layer.
12. When the user requests a small use case, do not expand it into the full
    lifecycle. A valid small example is a 12-month PD model using LTV, DSCR, and
    unemployment with a chronological split and basic calibration evidence.

## Open work in recommended order

### Immediate PD work

1. Retain prediction-level outputs for every candidate and period.
2. Add calibration intercept, slope, and reliability bins.
3. Add annual and rolling-origin backtests.
4. Add confidence intervals or bootstrap uncertainty for sparse-event metrics.
5. Add segment results and instability diagnostics.
6. Reconcile sampling-weighted metrics to full-population scores.
7. Assess recalibration without contaminating the comparison period.
8. Freeze candidates and document a human model-selection decision or defer it.

### LGD development

1. Reconcile default amount, cumulative loss, resolution state, recoveries,
   expenses, and timing.
2. Do not treat missing or unresolved loss as zero.
3. Establish a current empirical benchmark.
4. Build a classical two-part occurrence/severity candidate.
5. Test censoring, tail behavior, temporal performance, and segment stability.

### EAD development

1. Confirm funded-term-loan scope and available balance histories.
2. Use current UPB as the transparent benchmark.
3. Reconcile contractual amortization, interest-only periods, maturity,
   prepayment, modifications, and any future funding.
4. Build and test a contractual-plus-behavioral classical candidate.

### Expected-loss integration

1. Combine marginal PD, LGD, EAD, discounting, and scenarios at the controlled
   grain.
2. Reconcile loan-level results to portfolio totals.
3. Preserve scenario results before weighting.
4. Add sensitivity, limitation, and monitoring evidence.

### Publication work

1. Use the approved abstract as the basis for the first article.
2. Keep implemented evidence separate from future methodology.
3. Present the working prototype as available through GitHub.
4. Describe Hugging Face only as a possible later distribution channel.
5. Build the article first as the authoritative narrative and derive the slide
   deck from it.

## Human decision rights

The agent may recommend, implement research code, run tests, compare results,
and draft evidence. It must not independently approve:

- intended or prohibited use;
- default, loss, or exposure definitions;
- material exclusions or segmentation;
- final features or transformations;
- calibration or overlays;
- model selection;
- validation conclusions;
- limitations acceptance;
- production deployment.

Stop and request human direction when an unresolved decision would materially
change the target, population, methodology, interpretation, or permitted use.

## Required protocol for the fresh session

At the beginning of the new session:

1. Read the governing repository instructions and this restart prompt.
2. Inspect `git status`, recent commits, README, configurations, relevant code,
   tests, documentation, and external artifact manifests.
3. Verify that the local clone is synchronized with the intended GitHub branch.
4. Run the relevant tests before changing code.
5. Report any inconsistency between this handoff and repository evidence.
6. Preserve unrelated user changes and do not overwrite controlled artifacts.
7. State the lifecycle stage, requested outcome, assumptions, and open human
   decisions before substantive modeling work.
8. Implement the smallest coherent next increment, test it proportionately,
   update documentation, and report limitations.

For each task, return:

1. Outcome
2. Inputs and versions
3. Assumptions
4. Work completed
5. Findings
6. Tests and reconciliations
7. Artifacts created
8. Limitations
9. Human decisions required
10. Recommended next step

## New-session task interface

After pasting this prompt into a new session, append:

```text
Lifecycle stage:
Requested outcome:
Intended use:
Model component:
Data and files in scope:
Required output:
Required tests:
Known constraints:
Decisions already approved:
Decisions requiring human review:
```

If no task is appended, begin with a read-only repository and artifact audit,
then recommend the smallest next step. Do not make external or material changes
until the user requests implementation.
