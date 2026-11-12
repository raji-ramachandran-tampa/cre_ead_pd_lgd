# Publication manuscript workspace

Created November 2, 2026. Updated November 12, 2026. Status: working draft v0.2, not submission-ready.
This folder separates manuscript writing from model code and development evidence.
Model evidence remains in ../docs/model_development; restricted loan-level data,
serialized models and raw releases remain outside Git. Current modeling code
checkpoint `fcbf2b5` on ead-model-development. No arXiv submission has been initiated.

## Start here

- [Working manuscript](manuscript.md): abstract, introduction, methods, initial
  results and discussion; author/affiliation and PD quantitative results pending.
- [Claim register](evidence/claim_register.md): every central quantitative claim
  linked to its development evidence and population/metric limitations.
- [Source register](references/sources.md): citation audit and literature tasks.
- [Submission preparation](submission/README.md): eventual arXiv workflow.
- [Figures](figures/README.md) and [tables](tables/README.md): planned artifacts.

Working title: A Reproducible Public-Data Framework for Multifamily Credit Risk:
Default Timing, Signed Loss Severity, and Exposure Projection.

Proposed scope follows the original project: PD/LGD/EAD research plus documented
AI-assisted development. Do not claim integrated economicEL is empirically
validated or that AI assistance caused a measured productivity improvement.
Novelty and publication positioning require a fuller related-literature review.
An EAD-only article remains an option if the broader empirical scope is unsuitable.

## Writing sequence

1. Agree contribution, intended audience and target venue; confirm authorship.
2. Complete source-verified related work and PD results audit.
3. Reconcile populations/dates and reproduce manuscript tables from frozen reports.
4. Complete methods/results and uncertainty/robustness analyses proportionately.
5. Prepare publication figures, full bibliography, author/AI-use disclosures and
   data/code availability statement with actual license/access restrictions.
6. Convert settled manuscript to LaTeX; compile and inspect PDF; independently
   review all claims, citations, source package and latest submission requirements.
7. Author-led submission only after the completed paper is reviewed and authorized.

Markdown is the working source now, not an arXiv upload package. Keep future
LaTeX/PDF synchronized to the reviewed draft. Do not create a second divergent
manuscript. arXiv is a preprint venue; posting is not journal peer review.

## Latest update — November 12, 2026

The draft now includes prior-payment reconstruction,its limited coverage and
nonlinear recent-cohort overcorrection. EAD tables are regenerated from frozen
aggregate reports using [export_paper_ead_tables.py](../scripts/export_paper_ead_tables.py).
From the repository root, run:

```text
python scripts/export_paper_ead_tables.py --artifact-root <2026Q1-artifact-root> --paper-root paper --update-manuscript
```

[Table provenance](tables/ead_table_provenance.json) records input and exporter
hashes; this verifies transcription, not independent model validation. The
`paper/` workspace and exporter are included in the current GitHub EAD branch
checkpoint. Model binaries and raw/derived loan records remain external. No
arXiv upload or submission has been made. PD audit,full related work,authorship,
publication figures and a final submission package remain open.
