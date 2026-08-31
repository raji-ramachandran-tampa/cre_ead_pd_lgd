"""Simple, deterministic expected-loss summaries."""

from collections import defaultdict
from collections.abc import Iterable, Mapping


def summarize_expected_loss(
    rows: Iterable[Mapping[str, object]], group_by: str
) -> dict[object, float]:
    """Sum expected loss by one declared output field."""
    totals: dict[object, float] = defaultdict(float)
    for row in rows:
        if group_by not in row or "expected_loss" not in row:
            raise ValueError("Rows must contain the grouping field and expected_loss")
        totals[row[group_by]] += float(row["expected_loss"])
    return dict(totals)

