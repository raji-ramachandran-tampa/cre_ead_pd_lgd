# Model-development specification package

This directory translates the overarching CRE model governance and design into
implementable development requirements. It is a controlled working draft, not
evidence of completed development, validation, approval, or production use.

## Contents

- `specification.md` — development scope, definitions, architecture, evidence,
  testing, implementation, and governance requirements.
- `data_dictionary.md` — proposed loan-property-quarter data contract.
- `methodology_candidates.md` — benchmark, primary, and challenger methods for
  PD, LGD, EAD, scenarios, and aggregation.
- `acceptance_criteria.md` — objective entry, component, integration, evidence,
  and exit gates.
- `pandoc.yaml` — Pandoc settings for DOCX publication using the model-design
  Word reference template.

## Publication

After installing the project in its Python environment, publish with:

```text
cre-el build-doc --document model_development --source specification.md --output specification.docx
```

The command is Python. Pandoc remains an optional external dependency used only
for DOCX conversion.

The Markdown files are authoritative. Generated DOCX files are review copies
and must not contain content that is absent from the corresponding Markdown.
