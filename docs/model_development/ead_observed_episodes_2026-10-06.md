# EAD observed delinquency episodes — October 6, 2026

Lifecycle: development. User authorized episode-table construction. Status: executed
and tested diagnostic table, not approved contractual default/cure definitions,
model validation or expected-loss integration. Institutional owner TBD. Primary
EAD schedule method and frozen LGD targets unchanged. Local uncommitted work.

## Observed table and lineage

Implementation: models/ead_episodes.py. Inputs immutable monthly v0.3.0 and raw
2026Q1 Multifamily.zip. Source participation UPB joined at exact loan/report date;
identical selected-source rows collapsed and one-to-one join enforced. Source
accounting-parenthesis parser reused for numeric participation amounts. Old
monthly signed-loss parsing is not used; v0.3.0 not rebuilt or overwritten.
Processed histories restricted to reports strictly before source credit-event
resolution date when present. This restriction uses outcome metadata, appropriate
for diagnostics only, not historical prospective feature extraction.

170,272 observed history rows;2,416 spells over2,120 loans.238 loans have more than
one observed episode.2366 episode starts have positive participation UPB,50 do not.
Four uncertain left boundaries. End observations: return-to-non-SDQ1016,
history-end1395,history-gap5.750 loans have source resolution metadata. Of672
frozen signed LGD loans,660 have pre-resolution episodes and66 have multiple
observed spells.12 have no qualifying observed onset; not excluded from LGD.

## Algorithm and fields

SDQ is Y indicator OR60–89/90+ payment status. A spell starts at the first observed
SDQ report after non-SDQ, at history start, or after a missing-calendar-month gap.
Consecutive observed SDQ months continue the spell. Non-SDQ report ends it as
observed status transition;30–59 status is non-SDQ and is NOT necessarily current
or cured. Gap ends observable continuity without inferring cure/default recovery.
History start or gap marks uncertain next left boundary. History end does not
establish resolution or workout completion. Unknown/missing status or duplicate
history keys fails explicitly; no automatic boundary repair.

Episode fields: loan key/sequence, start/last observed SDQ dates, number observed
SDQ months, start scheduled and participation UPB, preceding report/status,
uncertain-left-boundary flag, end-observation type, following report/status,
source resolution date, last-episode-before-source-resolution diagnostic flag.
No episode is asserted as contractual default. Resolution date may relate to REO
sale or another disposition, not default onset. Last observed episode link is
hindsight association, not identification of the loss-producing episode.

## Use and restrictions

Use the table to investigate initial versus later observed exposures, repeated
status spells and source loss denominator differences. Do not choose the balance
closest to DefaultAmount and label its date as default. Do not use last-spell
information in initial prospective forecasts. Multiple observed spells do not
prove legally cured/redefaulted loans or independent defaults. Raw institution
participation exposure is not established whole-loan balance plus interest.

Next: summarize first-versus-last spell exposure differences on the66 repeatedly
observed signed-LGD loans; establish an explicit episode/default proposal aligned
with PD before any denominator adjustment. Keep initial principal forecast and
resolution-linked source loss outcomes separate. Exact interest/advance breakdown
still absent; no automatically computed total economic EAD or PD×LGD×EAD.

## Verification and reproduction

External immutable ead-observed-episodes-v0.1.0 contains observed_episodes.parquet
and report.json with raw/processed SHA256. No loan-level files in Git. Reproduce:
python -m cre_expected_loss.models.ead_episodes --root <Fannie-root> --output
<new-directory>. Tests: non-SDQ30–59 transition, history-gap continuity,
left boundary uncertainty, duplicate and unknown-status rejection. Full suite
113passed,5Pandoc skips,one existing pandas deprecation warning. Lint passes.
No previous model/artifact/label overwritten; rollback removes only additive
research code/table use and preserves original frozen source baseline.
