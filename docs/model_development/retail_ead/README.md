# Retail revolving EAD project

Started November16,2026 at user request. Branch `retail-ead-development`,forked
from EAD/paper checkpoint064983f. This is a separate consumer revolving-credit
research extension. Existing FannieCRE results and paper are inherited history,
not evidence of retail performance. No retail model fitted and no new retail
claims added to the manuscript. Independent validation/approval not established.

## Completed starter work

- Separate code package src/cre_expected_loss/retail_ead and configuration
  config/retail_ead.yaml,without modifying CRE forecast logic.
- CSV schema/quality auditor for original Home Credit card history and dictionary;
  input SHA256,duplicates,account/application mapping,missing/bad balances/limits,
  nonpositive available credit and provisional90DPD counts.
- Synthetic-tested provisional event/CCF contract: exact3/6/12month Current anchor,
  first observed90DPD event on the SAME card,history-gap/left-censor flags.
- Signed/unbounded CCF helper;negative and>1 results retained. Fully drawn or
  overlimit anchors have undefinedCCF but retain the principalEAD case.

These are implementation/synthetic checks,not an audit of actual Home Credit data.
User confirmed files are NOT downloaded. No real-data row counts,default rates,
model metrics or data/license acceptance are claimed.

## Obtain original source files

Use [Home Credit competition data](https://www.kaggle.com/competitions/home-credit-default-risk/data)
and review [source rules](https://www.kaggle.com/competitions/home-credit-default-risk/rules)
in your own Kaggle account. The automated browser reader returned no usable
body for these pages; no claim is made that access terms were reviewed/accepted.
Do not use unofficial mirrors as evidence of redistribution rights.

Extract `credit_card_balance.csv` and `HomeCredit_columns_description.csv` into
an external raw folder. Suggested layout outside repository:

```text
<HOME_CREDIT_ROOT>/raw/home-credit-default-risk-2018/
    credit_card_balance.csv
    HomeCredit_columns_description.csv
<HOME_CREDIT_ROOT>/artifacts/retail-ead-audit-v0.1.0/
```

Do not place archives,rawCSV,account identifiers or loan-level outputs inGit.
No credentials are requested or stored by the starter code.

## First real-data audit

From the repository root,using the project environment:

```text
python -m cre_expected_loss.retail_ead.audit --input-root <external-raw-folder> --output <new-external-artifact-folder>
```

The audit reads only the card CSV and hashes the supplied dictionary; dictionary
presence does not imply semantics have been reviewed. The expected field mapping
is provisional. Inspect source meanings,units,account closure/default status and
DPD semantics before creating a training target. Auditor does not fit a model or
automatically produce actual default labels.

## Research target proposal

Primary research options: direct balance at a declared future card-delinquency
proxy,or CCF=(eventbalance-anchorbalance)/(anchorlimit-anchorbalance). These are
retail exposure targets,not an amortization-ratio target and not an applicationPD.
ApplicationTARGET describes the current application; cannot attach it blindly to
past credit-card balances. Relative MONTHS_BALANCE permits within-account ordering,
not a verified calendar OOT split or direct macro joins. Group by linked application
for development splits,while auditing whether ultimate borrower identity is known.

Provisional first90DPD is an observable event definition,not established contractual
or regulatory default. Audit sample truncation,missing months,returns to Current,
limit reductions/closures,zero/negative balances and exposure components. Closed
accounts and limit reductions must not be interpreted as missing at random.
Denominator nearzero can makeCCF unstable;compare directEAD and CCF approaches.
Do not silently clip,drop negatives or censor values above1.

## Modeling sequence once the audit supports an outcome

1. Finalize documented event,balance/interest basis,units and cohort availability.
2. Build exact-horizon account-level pairs with eligibility reasons;retain raw data.
3. Benchmark hold balance and training-only utilization/CCF averages by segment.
4. Compare regularized regression and shallow nonlinear directEAD/CCF challengers.
5. Evaluate borrower/group separation,temporal limitations,bias,dollar errors,
   sparse segments,fully drawn accounts and uncertainty;no calendar OOT claim
   without actual dates. Report default-conditioned sampling explicitly.
6. Maintain separate publication evidence;do not pool retail and CRE observations
   or present consumer results as validating CRE revolving lines.

Next required input: original files plus dictionary/access-term review. Starter
code does not establish that Home Credit ultimately supports a publishable
realized-EAD target. If it does not,we will document that finding and consider
controlled-access corporate data rather than invent labels.

Verification November16:129 tests passed,five Pandoc-dependent checks skipped,
one existing pandas deprecation warning;retail module/test lint passes. Real-data
retail audit remains pending source files. External data folder prepared at
C:/Users/Rajir/data/retail_ead/raw/home-credit-default-risk-2018;no data downloaded.
