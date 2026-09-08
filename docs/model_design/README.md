# Model-design source and publishing

`content.md` is the authoritative narrative source for the CRE Model Governance
and Design Document.

Pandoc publishes the Markdown to Word. `pandoc.yaml` contains the conversion
settings, while `reference.docx` contains the approved Word styles, page setup,
headers, and footers. No custom Markdown parser is maintained in this project.

## Prerequisite

Install Pandoc and confirm that `pandoc --version` works in PowerShell.

## Build

After installing the project in its Python virtual environment, run:

```text
cre-el build-doc --document model_design --source content.md --output ../CRE_Expected_Loss_Model_Design.docx
```

To avoid replacing the controlled output during review, supply another path:

```text
cre-el build-doc --document model_design --source content.md --output preview.docx
```

## Tests

Run the repository's self-contained document tests with:

```text
cre-el test
```

The tests check the Markdown source, Pandoc configuration, reference DOCX,
heading and table preservation, hyperlinks, and the generated DOCX package.
Integration tests are skipped locally when Pandoc is unavailable. GitHub
Actions installs Pandoc and runs the complete test suite on every push and pull
request.

## Editing workflow

1. Edit and review `content.md`.
2. Run the Python `cre-el build-doc` command, which invokes optional Pandoc
   using `pandoc.yaml` and `reference.docx`.
3. Render and visually inspect the DOCX.
4. Run accessibility, heading, section, hyperlink, and table-geometry checks.
5. Commit both the reviewed Markdown and regenerated DOCX.

Do not edit the generated DOCX without carrying the same change back into
`content.md`; otherwise the next build will overwrite it.
