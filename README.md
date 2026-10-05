# CRE EAD, PD, LGD and Expected Loss

Governance and design foundation for a Commercial Real Estate expected-loss
framework covering Probability of Default (PD), Loss Given Default (LGD),
Exposure at Default (EAD), scenarios, validation, and ongoing performance
assessment.

The repository now also contains the first development implementation slice:
validated PD term structures, discounted workout LGD, contractual EAD,
scenario controls, expected-loss aggregation, transparent CRE features, and
DuckDB/Parquet ingestion utilities. These are development components, not a
fitted, validated, or approved model.

## Current contents

- `docs/CRE_Expected_Loss_Model_Design.docx` — overarching model governance and
  design document aligned to SR 26-2, with a legacy SR 11-7 crosswalk.
- `docs/model_design/content.md` — authoritative, reviewable narrative source.
- `docs/model_design/pandoc.yaml` — reproducible Markdown-to-Word settings.
- `docs/model_design/reference.docx` — approved Word styles and page layout.
- `src/cre_expected_loss/cli.py` — Python-only project command interface.
- `tests/test_model_design_document.py` — source, configuration, and generated
  DOCX unit and integration tests.
- `.github/workflows/document-tests.yml` — complete Pandoc build verification
  on pushes and pull requests.
- `docs/model_development/` — proposed development specification, data
  dictionary, methodology candidates, and objective acceptance gates.
- `src/cre_expected_loss/` — reusable model-development calculations and data
  interfaces.
- `config/` — proposed model and scenario configuration.
- `docs/data_sources/` and `config/public_sources.yaml` — controlled public-data
  selection, source-to-field mapping, access registry, and acquisition sequence.
- `docs/model_development/comparative_methodology_plan.md` — common-sample
  classical, Bayesian, and machine-learning comparison for PD, LGD, and EAD.
- `tests/` — document, mathematical, contract, boundary, and integration tests.
- `data/raw`, `data/interim`, `data/processed` — ignored local data layers;
  only directory placeholders are versioned.

Restricted Fannie Mae loan data default to `C:/Users/Rajir/data/fanniemae`.
Set `FANNIE_MFLPD_ROOT` only when you need to override that location. See `.env.example` and
`config/data_locations.yaml`. Do not place Data Dynamics credentials in project
files.

## Restart in a new AI session

Use the following instruction after clearing or replacing the current
conversation:

> Open the `cre_ead_pd_lgd` repository and read `AGENTS.md`,
> `docs/prompts/CRE_PROJECT_META_PROMPT.md`, and
> `docs/prompts/CRE_PROJECT_RESTART_PROMPT_2026-10-05_LGD_BASELINE.md`. Follow the
> fresh-session protocol in the Phase 1 restart prompt. Begin with a read-only
> audit and report any inconsistency before continuing development.

The restart prompt is a versioned handoff, not authoritative evidence. Verify
its status and results against the current repository, external manifests, and
generated artifacts before relying on them. Raw data and credentials remain
outside Git.

## LGD Development Restart Point (2026-10-05)

Read `docs/model_development/lgd_development_2026-10-05.md` after the Phase 1 handoff.
LGD reconciliation is implemented and executed on the external 2026Q1 v0.3.0 dataset.
A two-part research fitting pipeline is implemented and tested on synthetic data.
Real-data fitting is pending human direction on the proposed Fannie Mae net-loss-ratio
target, which differs from discounted economic workout LGD. No severity model has
been fitted or selected in this increment.

## Developer setup

```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
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

# Compare fitted baseline, revised-macro, and vintage-aware candidates
cre-el compare-fannie-pd --release 2026Q1
```

The data and modeling application runs entirely in the active Python virtual
environment. Pandoc remains an optional external dependency used only when the
Python `cre-el build-doc` command is asked to publish Markdown as DOCX.
- `docs/prompts/CRE_PROJECT_META_PROMPT.md` — durable lifecycle instructions for
  future design, coding, validation, monitoring, and documentation work.
- `docs/prompts/CRE_PROJECT_RESTART_PROMPT_2026-10-05_LGD_BASELINE.md` — dated Phase
  1 implementation handoff for restarting the project in a fresh AI session.
- `docs/prompts/tasks/` — focused templates for model development, validation,
  ongoing performance assessment, and lifecycle documentation.
- `AGENTS.md` — repository instructions that apply the meta-prompt to future
  work.

## Status

This repository is in model development with fitted classical research candidates and a synthetic collateral-recovery baseline. It does not yet contain
an approved production model, completed independent validation, or production
monitoring evidence. Documentation should be described as aligned to applicable
guidance, not as proof of regulatory compliance.

## Next stages

1. Review the proposed development specification and complete the regulatory
   applicability and enterprise-policy map.
2. Approve model purpose, population, default/LGD/EAD definitions, data
   contract, candidate plan, and acceptance standards.
3. Build the reproducible data and model-development pipeline against the
   approved specification.
4. Perform objective validation and implementation verification.
5. Establish approved monitoring metrics, thresholds, escalation, and periodic
   performance assessment.

## October 5 LGD research baseline

See `docs/prompts/CRE_PROJECT_RESTART_PROMPT_2026-10-05_LGD_BASELINE.md` for
the current handoff. The baseline preserves signed source net-loss ratios,
mean/ridge/hurdle comparisons, allocation/outcome audits, and a synthetically
tested collateral waterfall. No model is selected or production approved.
Run `cre-el test` for the complete pytest suite, including function-style LGD tests.
Raw data and generated loan-level results remain outside Git.
