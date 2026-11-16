"""Provisional account-level delinquency EAD/CCF targets, not verified defaults."""

import numpy as np
import pandas as pd

COLUMNS = ["account_id", "month_index", "drawn_balance", "credit_limit", "days_past_due"]


def conversion_factor(balance, limit, ead):
    """Signed/unbounded CCF; fully drawn/overlimit anchors have undefined CCF."""
    values = np.asarray([balance, limit, ead], dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Finite nonnegative exposure inputs required")
    return float((ead - balance) / (limit - balance)) if limit > balance else float("nan")


def proxy_pairs(monthly, horizons=(3, 6, 12), dpd_threshold=90):
    """Use first observed threshold crossing; exact current-status anchor.

    Account-relative months cannot establish calendar OOT splits. Every returned
    row retains an eligibility reason; missing/default/censoring is never imputed.
    Only a proposed historical delinquency proxy, not application TARGET mapping.
    """
    if not set(COLUMNS).issubset(monthly):
        raise ValueError("Missing monthly fields")
    if (
        not horizons
        or len(set(horizons)) != len(horizons)
        or any(isinstance(h, bool) or not isinstance(h, int) or h <= 0 for h in horizons)
    ):
        raise ValueError("Distinct positive integer horizons required")
    if isinstance(dpd_threshold, bool) or not isinstance(dpd_threshold, int) or dpd_threshold <= 0:
        raise ValueError("Positive integer delinquency threshold required")
    f = monthly[COLUMNS].copy()
    if (
        f[["account_id", "month_index"]].isna().any().any()
        or f.duplicated(["account_id", "month_index"]).any()
    ):
        raise ValueError("Missing or duplicate account/month keys")
    if not np.isfinite(f.month_index).all() or not f.month_index.mod(1).eq(0).all():
        raise ValueError("Integer account-relative month index required")
    rows = []
    for account, g in f.groupby("account_id", sort=False):
        g = g.sort_values("month_index")
        events = g[g.days_past_due.ge(dpd_threshold)]
        if events.empty:
            continue
        event = events.iloc[0]
        for horizon in horizons:
            record = {
                "account_id": account,
                "event_month": int(event.month_index),
                "horizon_months": horizon,
                "eligibility": "eligible_delinquency_proxy",
                "anchor_balance": np.nan,
                "anchor_limit": np.nan,
                "event_balance": event.drawn_balance,
                "event_limit": event.credit_limit,
                "ccf": np.nan,
                "ccf_status": "not_computable",
                "event_definition": f"first_observed_{dpd_threshold}dpd_proxy",
            }
            anchor = g[g.month_index.eq(event.month_index - horizon)]
            if event.month_index == g.month_index.min():
                record["eligibility"] = "left_censored_event"
            elif anchor.empty:
                record["eligibility"] = "missing_exact_anchor"
            else:
                a = anchor.iloc[0]
                record["anchor_balance"], record["anchor_limit"] = a.drawn_balance, a.credit_limit
                window = g[g.month_index.between(a.month_index, event.month_index)]
                valid = np.asarray(
                    [a.drawn_balance, a.credit_limit, event.drawn_balance, event.credit_limit],
                    dtype=float,
                )
                if len(window) != horizon + 1:
                    record["eligibility"] = "history_gap"
                elif (
                    not np.isfinite(window.days_past_due).all() or window.days_past_due.lt(0).any()
                ):
                    record["eligibility"] = "unknown_delinquency_history"
                elif a.days_past_due != 0:
                    record["eligibility"] = "anchor_not_current"
                elif not np.isfinite(valid).all() or (valid < 0).any():
                    record["eligibility"] = "invalid_or_credit_exposure_needs_review"
                else:
                    record["ccf"] = conversion_factor(
                        a.drawn_balance, a.credit_limit, event.drawn_balance
                    )
                    record["ccf_status"] = (
                        "positive_undrawn"
                        if a.credit_limit > a.drawn_balance
                        else "fully_drawn_or_overlimit"
                    )
            rows.append(record)
    return pd.DataFrame(rows)
