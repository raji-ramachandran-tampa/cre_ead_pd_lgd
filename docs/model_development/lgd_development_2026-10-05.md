# LGD development baseline — October 5, 2026

The baseline includes source-sign parser correction, nonnegative historical fits,
signed mean/ridge/hurdle models, source allocation and outcome audits, a synthetic
collateral waterfall and complete pytest discovery. User accepted signed-source
research. No model selected or independently validated.

Full signed sample: 672, split 632 training, 29 validation, 11 examined OOT.
No monthly dataset or earlier fit was overwritten. External versioned artifacts
remain outside Git. Complete baseline verification: 75 passed, five Pandoc checks
skipped. Reproduction scripts accept external paths; no machine-bound paths.

Next work: reconcile source allocation/finalization, define default episodes
jointly with PD, collect verified collateral input contracts and evaluate future
increments chronologically. Existing EL aggregation does not accept arbitrary
signed source loss as projected economic LGD.

## Scope and evidence restrictions

Status: development research, not institutional approval or independent validation.
Detailed source case records, identifiers, financial amounts, locations and dates
are retained only in restricted external artifacts and local review documents.
This repository record contains aggregate evidence. Models are frozen and no
case exclusion or target change is approved by this document.

See `../prompts/CRE_PROJECT_RESTART_PROMPT_2026-10-05_LGD_BASELINE.md` for the
current verified handoff. The signed source net-loss ratio and synthetic economic
collateral calculations are separate outcomes; no economic expected-loss integration
or production use is established. Source revisions and availability remain open.
