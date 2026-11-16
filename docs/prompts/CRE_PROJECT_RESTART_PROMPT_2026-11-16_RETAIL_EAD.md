# Restart — November 16, 2026: separate retail EAD extension

Read rootAGENTS,meta prompt and model-development task. Active branch
retail-ead-development,from064983f. User authorized separate retail branch and
starting project. CRE EAD branch and main unchanged. Project entry:
docs/model_development/retail_ead/README.md; config/retail_ead.yaml.

Candidate source Home Credit Default Risk2018. User confirmed NOT downloaded.
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
