"""Portable data-contract checks."""

from collections.abc import Iterable, Mapping


def assert_unique_keys(rows: Iterable[Mapping[str, object]], keys: tuple[str, ...]) -> None:
    """Raise on missing, null, or duplicate composite keys."""
    if not keys:
        raise ValueError("At least one key is required")
    seen: set[tuple[object, ...]] = set()
    for row_number, row in enumerate(rows, start=1):
        try:
            key = tuple(row[name] for name in keys)
        except KeyError as exc:
            raise ValueError(f"Missing key {exc.args[0]!r} in row {row_number}") from exc
        if any(value is None or value == "" for value in key):
            raise ValueError(f"Null or blank key in row {row_number}")
        if key in seen:
            raise ValueError(f"Duplicate key {key!r}")
        seen.add(key)

