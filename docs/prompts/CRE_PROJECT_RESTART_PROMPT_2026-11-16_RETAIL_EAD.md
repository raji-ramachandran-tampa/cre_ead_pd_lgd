# Restart — November 16, 2026: separate retail EAD extension

Read rootAGENTS,meta prompt and model-development task. Active branch
retail-ead-development,from064983f. User authorized separate retail branch and
starting project. CRE EAD branch and main unchanged. Project entry:
docs/model_development/retail_ead/README.md; config/retail_ead.yaml.

Candidate source Home Credit Default Risk2018. Initially not downloaded;see current receipt below.
Original card CSV and column dictionary needed from Kaggle after source terms
review; automated web reader could not inspect data/rules body. No authentication
or license acceptance performed. Raw data must stay outsideGit,HOME_CREDIT_ROOT
external path. No real retail data audited or model fitted.

Completed audit starter and generic provisional target helpers in separate
cre_expected_loss.retail_ead package. Auditor computes schema/quality/hash report,
not targets/model. Provisional first90DPD and exact3/6/12month Current anchors,
missing-history/left-censor flags,unboundedCCF,undefined fullydrawnCCF preserving
EAD rows. ApplicationTARGET cannot label historical card default. Field semantics,
units,currency and actual default remain pending official dictionary review.
MONTHS_BALANCE relative offsets cannot prove calendar OOT or macro alignment.

Next: obtain original credit_card_balance.csv,HomeCredit_columns_description.csv,
audit actualschema/data,review terms/dictionary,decide whether target identifiable.
Only then build empirical datasets and benchmarkdirectEAD/CCF. Do not fabricate
rows,missing exposure components or results. Retail scope distinct fromCRE paper;
no pooled validation/integratedEL or institutional approval. Preserve existing
FannieLGD/EAD results and publication draft. Git log records branch checkpoint.

Verification November16:129 tests passed,five Pandoc-dependent checks skipped,
one existing pandas deprecation warning;retail module/test lint passes. Real-data
retail audit remains pending source files. External data folder prepared at
C:/Users/Rajir/data/retail_ead/raw/home-credit-default-risk-2018;no data downloaded.

## Real files received and audited — November 16, 2026

User placed card ZIP/dictionary in external retail_ead root. Originals preserved,
CSV safely extracted and dictionary copied to prepared raw directory. Executed
audit:3,840,312 rows,104,307 cards,zero duplicatekeys/missing numeric core values.
Dictionary219rows,23card entries,cp1252. Core definitions reviewed;access terms
not independently verified. Raw90DPD1806 accounts,tolerance90DPDonly39. First
raw event medianbalance207.0225rawunits,70zero balances;proposeddefault validity
requires materiality review. No model fitted. External reportsretail-ead-audit-v0.1.0,
retail-ead-source-review-v0.1.0,retail-ead-file-receipt-v0.1.0. See retail_ead/
data_receipt_audit_2026-11-16.md. Next inspect raw/tolerance differences and balance
materiality before target/CCF model. These updates local/uncommitted;no data inGit.

## Real-data target/benchmark test — November 16, 2026

User authorized testing. See retail_ead/real_data_test_2026-11-16.md. External
retail-ead-proxy-test-v0.1.0. Raw90DPD eligiblepairs34/1325/1408 at3/6/12months;
tolerance90DPD0/12/15. Fixedgroup minimum60train/20heldout. Onlyraw6/12month
simple nonnegativeEAD-ratio regression fitted;heldout260/294 using stableapplication
hash,NOTcalendarOOT. RegressionMAE4221.37/4749.84rawunits,worse than meanlimitratio
4169.71/4744.19. Aggregate errors293.7%/181.7% of eventbalances,not accuracy.
Negative CCF preserved;unconstrainedmeanCCF yields invalidnegativeEAD225/256 and
248/278. No clipping. Tolerance model skipped. No selected/validated retailEAD
model;primary data feasibility unresolved. Do not respond by fitting more complex
models to poor labels. Next:materiality/balance composition review and alternative
true-default data access. Source/CRE models unchanged;raw artifacts outsideGit.

Verification November16:132 tests passed,five Pandoc skips;one existing pandas
deprecation warning. New experiment/test lint passes. Source implementation hash
verified against executed artifact;554heldout horizon predictions reload-match.
