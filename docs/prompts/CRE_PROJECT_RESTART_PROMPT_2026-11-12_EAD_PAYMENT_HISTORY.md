# CRE restart — November 12, 2026: payment-history EAD refinement

Read AGENTS.md,meta prompt,model-development task. Branch ead-model-development.
User requested advancing EAD. See docs/model_development/ead_payment_history_2026-11-12.md.
Prior advanced checkpoint0d3b73c preserved. Primary remains deterministic amortization
with provisional postIO clock and flagged holds; nonlinear/ridge diagnostic only.

Completed diagnosis: recent nonlinear schedule correction too large. At12m needed
0.06801% aggregate correction,boosted0.28106%; no recalibration to recent outcomes.
Tested3month prior-payment reconstruction with fixed stability gate,Current-only
history and known fixed/pre-maturity contract. Exact prior reference identity3867
rows. Limited coverage111/115 totalaccepted3/12months,only6/4recent. Full eligible
recent error0.10836%/0.54087% versus0.11093%/0.54619%reference. Supported recent
0.02256%/0.19323%,tiny gain. No new primary selection or broad improvement claim.

Final external ead-payment-history-v0.1.1 hashes inputs/code; initialv0.1.0 diagnostic
preserved. No loan-level records inGit,no PD/LGD change,CCF/economicEAD or EL claim.
Next: understand payment/reporting instability and improve actual contract schedule
availability; do not relax gates using examined recent outcomes. Uncertainty drift
and exposure/default basis still unresolved. Retain older findings and references.

Local paper/ draft and November2 handoff manuscript note predate this task and are
not included in this modeling checkpoint; do not accidentally publish paper files.
No arXiv submission. Current work adds only model code,synthetic tests and aggregate
evidence/handoff. Check Git log for latest pushed branch commit.

Verification November12:124 tests passed,five Pandoc-dependent skips;one existing
pandas deprecation warning. New module/test lint passes.

## Paper and source upload — November 12, 2026

User requested paper update and code upload. paper/manuscript.md draftv0.2 now
includes payment-history results/coverage and nonlinear correction drift. Paper
workspace and scripts/export_paper_ead_tables.py included on GitHub EAD branch;
model codefcbf2b5 already published. Exporter reads frozen aggregate reports only,
checks paired samples and regenerates both EAD tables with input/code hashes.
Paper remains work in progress:PD evidence,literature/authorship and final figures
open. No arXiv submission or loan-level Git data. Original modeling checkpoint
excluded paper; this later publication-workspace checkpoint supersedes that status.
