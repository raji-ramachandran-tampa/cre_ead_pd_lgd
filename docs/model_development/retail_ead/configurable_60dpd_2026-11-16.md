# Configurable delinquency and60DPD experiment — November 16, 2026

Lifecycle: development. User explicitly requested configurable delinquency and
60days. Implemented60DPD research proxy,not contractual/regulatory default.
Separate retail branch;existing90day/CRE artifacts and manuscript unchanged.
No institutional model selection,approval or independent validation inferred.

## Configuration and interface

config/retail_ead.yaml default_proxy.threshold_days is now60. CLI loads this YAML
and horizons_months (3,6,12);--dpd-threshold overrides the threshold. Validate
positive integer days,distinct positive integer horizons;bool/zero invalid.
Threshold flows into account selection,first-crossing target creation,definition
names,modelkeys and report. Generic proxy helper default60;explicit90 remains
supported. Empty event/eligible cohorts produce reports without model fits.
Saved reports include effective settings,configuration snapshot/hash and source
hash;config_used.yaml preserves exact input even when current YAML changes later.
Historical audit90DPD counts remain descriptive90day facts,not active target.

Default run from repo root:
python -m cre_expected_loss.retail_ead.experiment --root <HOME_CREDIT_ROOT>
--config config/retail_ead.yaml --output <new-directory>

90day sensitivity:
same command with --dpd-threshold 90 and a different new output directory.
No overwrite of existing outputs. Current/nonSDQ anchor is defined under the
selected raw/tolerance measure. Other eligibility/group/model rules unchanged.

## Event and usable-case comparison

| Definition | Event accounts90days | Event accounts60days |
|---|---:|---:|
| RawDPD | 1806 | 2192 |
| Small-debt-tolerantDPD | 39 | 114 |

| Horizon | Raw90 eligible | Raw60 eligible | Tolerance90 eligible | Tolerance60 eligible |
|---|---:|---:|---:|---:|
| 3months | 34 | 1787 | 0 | 51 |
| 6months | 1325 | 1711 | 12 | 43 |
| 12months | 1408 | 1640 | 15 | 43 |

Counts are horizon-case pairs,not independent new loans. First crossing and
exposure date change when threshold changes;60day and90day results are different
targets/cohorts,not a paired improvement experiment. The user chose60days;not
selected by benchmark performance or to claim default identification.

##60day fitting and results

Raw60 positive-anchor-limit training/heldout groups:3m1388/341,6m1366/336,
12m1309/326. Exploratory nonnegative directEAD/limit regression fitted at all3
horizons;1003heldout horizon cases reload-match. Tolerance60 groups34/7,35/8,
32/11;all below unchanged minimum60train/20heldout,so fits skipped. Zero-limit
EAD pairs retained but excluded from ratio fit:raw58/9/5,tolerance10/0/0.

| Raw60 horizon | Heldout cases | HoldbalanceMAE | MeanEAD/limitMAE | DirectregressionMAE |
|---|---:|---:|---:|---:|
| 3months | 341 | 3444.50 | 10569.69 | 9954.05 |
| 6months | 336 | 30398.88 | 11093.68 | 11118.63 |
| 12months | 326 | 58124.50 | 12330.62 | 12356.65 |

MAE raw source amount units,not verified currency. Hold is strongest3month
benchmark;regression fails to beat meanlimitratio6/12month. Raw regression
aggregate errors202.18%,208.88%,174.41%of observed eventbalances,not accuracy.
No predictive superiority or production fitness. Application-hash split not
calendarOOT;relative dates and selected applicant histories remain limitations.

CCF kept unbounded. Raw60 definedCCF1714/1615/1518;negative465/1036/1274,
aboveone32/27/30. Tolerance60 defined28/32/27,aboveone11/14/15. Nonpositive
undrawn retainsEADcase/undefinedCCF. UnconstrainedmeanCCF produces negativeEAD
297/326 at6m and257/303 at12m;reported invalid,not clipped or selected.
Materiality/balance composition and event definition still require investigation;
114 tolerance60 accounts do not imply enough eligible current-anchor observations.

## Provenance and verification

Final immutable retail-ead-proxy-test-60dpd-v0.1.1:all pairs,heldout predictions,
models,report and exactconfig snapshot outsideGit. Initial60v0.1.0 retained as
metadata-stage diagnostic. Original90 retail-ead-proxy-test-v0.1.0 preserved.
Configurable90 replay retail-ead-90dpd-config-replay-v0.1.0 reproduces original
counts,eligibility,split sizes and MAE withinrtol1e-10;proves threshold plumbing
retains previous behavior. No source or prior model overwritten.

Tests verify YAML/default/override validation,changed first-event dates and anchor
balances,empty-run behavior,existing feature timing/group contracts. Full-suite
result below. No new data inGit,no CRE integration,paper relabeling or arXiv action.
Next:inspect60day materiality and balance/limit behavior using this declared proxy;
do not loosen minimum sample gates or relabel it as90day default.

Verification:135 tests passed,five Pandoc-dependent skips;one existing pandas
deprecation warning. Retail code/tests lint passes. Saved60day config/source
hashes verified and1003heldout predictions reload-match.
