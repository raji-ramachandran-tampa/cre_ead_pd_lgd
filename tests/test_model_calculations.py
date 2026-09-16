"""Unit tests for the first expected-loss implementation slice."""

import importlib.util
import math
import sys
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cre_expected_loss.aggregation import (
    ExpectedLossRow,
    aggregate_scenario_weighted_loss,
    calculate_expected_loss,
)
from cre_expected_loss.features import (
    debt_service_coverage_ratio,
    loan_to_value,
    valuation_age_days,
)
from cre_expected_loss.ingestion import csv_to_parquet
from cre_expected_loss.ingestion.fannie import inspect_zip, write_manifest
from cre_expected_loss.ingestion.macro import (
    FRED_SERIES,
    build_alfred_initial_release_features,
    build_monthly_macro_features,
    download_alfred_initial_releases,
)
from cre_expected_loss.models import (
    WorkoutCashFlow,
    binary_metrics,
    discounted_workout_lgd,
    empirical_lgd,
    fit_logistic_pd,
    fit_segment_pd_benchmark,
    funded_term_ead,
    hazards_to_term_structure,
    project_contractual_ead,
)
from cre_expected_loss.paths import fannie_data_root, fannie_release_directory
from cre_expected_loss.scenarios import validate_scenario_weights
from cre_expected_loss.validation import assert_unique_keys


class PDTermStructureTest(unittest.TestCase):
    def test_hazards_reconcile_to_survival_and_cumulative_pd(self) -> None:
        result = hazards_to_term_structure([0.10, 0.20, 0.25])
        for actual, expected in zip(result.marginal_pd, (0.10, 0.18, 0.18), strict=True):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(result.survival, (0.90, 0.72, 0.54), strict=True):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(result.cumulative_pd, (0.10, 0.28, 0.46), strict=True):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(result.cumulative_pd[-1] + result.survival[-1], 1.0)

    def test_invalid_hazards_fail_explicitly(self) -> None:
        for hazards in ([], [-0.1], [1.1], [math.nan]):
            with self.subTest(hazards=hazards), self.assertRaises(ValueError):
                hazards_to_term_structure(hazards)


class LGDTest(unittest.TestCase):
    def test_discounted_workout_lgd(self) -> None:
        cash_flows = [
            WorkoutCashFlow(60.0, 1.0, "recovery"),
            WorkoutCashFlow(10.0, 1.0, "cost"),
        ]
        self.assertAlmostEqual(discounted_workout_lgd(100.0, cash_flows, 0.10), 6 / 11)

    def test_raw_lgd_is_not_silently_capped(self) -> None:
        result = discounted_workout_lgd(100.0, [WorkoutCashFlow(20.0, 0.0, "cost")], 0.0)
        self.assertEqual(result, 1.2)

    def test_provisional_empirical_lgd_is_uncapped(self) -> None:
        self.assertEqual(empirical_lgd(120.0, 100.0), 1.2)
        with self.assertRaises(ValueError):
            empirical_lgd(1.0, 0.0)


class EADTest(unittest.TestCase):
    def test_contractual_projection_reconciles_payments_and_draws(self) -> None:
        self.assertEqual(
            project_contractual_ead(100.0, [10.0, 20.0, 70.0], [5.0, 0.0, 0.0]),
            (95.0, 75.0, 5.0),
        )

    def test_commitment_limit_is_enforced(self) -> None:
        with self.assertRaises(ValueError):
            project_contractual_ead(90.0, [0.0], [20.0], commitment_limit=100.0)

    def test_funded_term_ead_benchmark(self) -> None:
        self.assertEqual(funded_term_ead(125.0), 125.0)
        with self.assertRaises(ValueError):
            funded_term_ead(-1.0)


@unittest.skipUnless(importlib.util.find_spec("sklearn"), "scikit-learn is not installed")
class ClassicalPDTest(unittest.TestCase):
    def test_binary_metrics(self) -> None:
        result = binary_metrics([0, 0, 1, 1], [0.1, 0.2, 0.7, 0.9])
        self.assertEqual(result.observations, 4)
        self.assertEqual(result.events, 2)
        self.assertEqual(result.roc_auc, 1.0)
        with self.assertRaises(ValueError):
            binary_metrics([0, 1], [0.1, 1.1])

    def test_weighted_logistic_pd_fit(self) -> None:
        import pandas as pd

        frame = pd.DataFrame(
            {"x": [0.0, 1.0, 2.0, 3.0], "segment": ["A", "A", "B", "B"], "event": [0, 0, 1, 1]}
        )
        model = fit_logistic_pd(
            frame,
            "event",
            ["x"],
            ["segment"],
            class_weight=None,
            sample_weight=[2.0, 2.0, 1.0, 1.0],
        )
        probability = model.predict_proba(frame[["x", "segment"]])[:, 1]
        self.assertTrue(all(0.0 <= value <= 1.0 for value in probability))


class AggregationTest(unittest.TestCase):
    def test_expected_loss_identity_and_grain_are_preserved(self) -> None:
        row = ExpectedLossRow("L1", "P1", 1, "baseline", 0.02, 0.40, 1_000.0, 0.95)
        result = calculate_expected_loss([row])[0]
        self.assertAlmostEqual(result["expected_loss"], 7.6)
        self.assertEqual(result["scenario_id"], "baseline")

    def test_scenario_weighted_loss_uses_validated_weights(self) -> None:
        rows = [
            ExpectedLossRow("L1", "P1", 1, "baseline", 0.01, 0.5, 100.0),
            ExpectedLossRow("L1", "P1", 1, "adverse", 0.03, 0.5, 100.0),
        ]
        self.assertAlmostEqual(
            aggregate_scenario_weighted_loss(rows, {"baseline": 0.75, "adverse": 0.25}),
            0.75,
        )

    def test_invalid_expected_loss_inputs_fail(self) -> None:
        with self.assertRaises(ValueError):
            _ = ExpectedLossRow("L1", "P1", 1, "baseline", 1.1, 0.4, 100.0).expected_loss


class ContractAndFeatureTest(unittest.TestCase):
    def test_scenario_weights(self) -> None:
        validate_scenario_weights({"baseline": 0.6, "adverse": 0.4})
        with self.assertRaises(ValueError):
            validate_scenario_weights({"baseline": 0.7, "adverse": 0.4})

    def test_unique_composite_keys(self) -> None:
        rows = [{"loan_id": "L1", "property_id": "P1", "as_of": "2026-06-30"}]
        assert_unique_keys(rows, ("loan_id", "property_id", "as_of"))
        with self.assertRaises(ValueError):
            assert_unique_keys(rows + rows, ("loan_id", "property_id", "as_of"))

    def test_transparent_features(self) -> None:
        self.assertEqual(loan_to_value(80.0, 100.0), 0.8)
        self.assertEqual(debt_service_coverage_ratio(125.0, 100.0), 1.25)
        self.assertEqual(valuation_age_days(date(2026, 1, 1), date(2026, 1, 31)), 30)

    def test_fannie_path_comes_from_environment(self) -> None:
        configured = str(Path.cwd() / "external-fannie-test")
        with patch.dict("os.environ", {"FANNIE_MFLPD_ROOT": configured}):
            self.assertEqual(fannie_data_root(), Path(configured).resolve())
            self.assertEqual(
                fannie_release_directory("2026Q1"),
                Path(configured).resolve() / "raw" / "2026Q1",
            )
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                fannie_data_root(),
                Path(r"C:\Users\Rajir\data\fanniemae"),
            )

    def test_invalid_fannie_release_fails(self) -> None:
        with patch.dict("os.environ", {"FANNIE_MFLPD_ROOT": str(Path.cwd())}):
            for release in ("2026", "26Q1", "2026Q5", "abcdQ1"):
                with self.subTest(release=release), self.assertRaises(ValueError):
                    fannie_release_directory(release)


@unittest.skipUnless(importlib.util.find_spec("duckdb"), "DuckDB is not installed")
class DuckDBIntegrationTest(unittest.TestCase):
    def test_csv_snapshot_converts_to_parquet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sample.csv"
            output = Path(directory) / "sample.parquet"
            source.write_text("loan_id,balance\nL1,100\n", encoding="utf-8")
            self.assertEqual(csv_to_parquet(source, output), output)
            self.assertTrue(output.is_file())

    def test_segment_pd_benchmark_writes_versioned_artifacts(self) -> None:
        import duckdb

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, artifacts = root / "monthly.parquet", root / "artifacts"
            duckdb.sql(
                """COPY (SELECT * FROM (VALUES
                ('L1', DATE '2018-01-01', DATE '2010-01-01', NULL, 'Multifamily', 0),
                ('L2', DATE '2018-02-01', DATE '2011-01-01', DATE '2018-02-15', 'Multifamily', 1),
                ('L3', DATE '2020-01-01', DATE '2012-01-01', NULL, 'Multifamily', 0),
                ('L4', DATE '2024-01-01', DATE '2013-01-01', DATE '2024-01-15', 'Multifamily', 1)
                ) t(loan_id, reporting_date, acquisition_date, first_credit_event_date,
                    property_type, proposed_default_event)) TO ? (FORMAT PARQUET)""",
                params=[str(source)],
            )
            result = fit_segment_pd_benchmark(
                source,
                artifacts,
                train_end=date(2018, 12, 31),
                validation_end=date(2022, 12, 31),
                smoothing_observations=10.0,
            )
            self.assertEqual(result["metrics"]["train"]["events"], 1)
            self.assertTrue((artifacts / "segment_rates.parquet").is_file())
            self.assertTrue((artifacts / "model_report.json").is_file())


class FannieIntakeTest(unittest.TestCase):
    def test_dscr_zip_is_inspected_without_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "Multifamily_DSCR.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("dscr.csv", "Loan Number,Year,Year DSCR\nL1,2025,1.25\n")
            result = inspect_zip(archive_path, "dscr", count_rows=True)
            self.assertEqual(result["column_count"], 3)
            self.assertEqual(result["data_row_count"], 1)
            self.assertEqual(len(result["archive_sha256"]), 64)
            self.assertFalse((Path(directory) / "dscr.csv").exists())

    def test_manifest_cannot_be_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "manifest.json"
            write_manifest({"release": "2026Q1"}, destination)
            with self.assertRaises(FileExistsError):
                write_manifest({"release": "2026Q1"}, destination)


class MacroIntakeTest(unittest.TestCase):
    def test_monthly_macro_panel_applies_lags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw" / "fred" / "2026-01-01"
            raw.mkdir(parents=True)
            for series_id in FRED_SERIES:
                (raw / f"{series_id}.csv").write_text(
                    f"observation_date,{series_id}\n2024-01-01,1.0\n2025-01-01,2.0\n",
                    encoding="utf-8",
                )
            result = build_monthly_macro_features(root, "2026-01-01")
            self.assertEqual(result["series"]["UNRATE"]["first_available_month"], "2024-02-01")
            self.assertEqual(result["series"]["RRVRUSQ156N"]["first_available_month"], "2024-03-01")
            self.assertTrue((root / "processed" / "2026-01-01" / "macro_monthly.parquet").is_file())

    def test_alfred_initial_release_panel(self) -> None:
        import json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw" / "alfred_initial" / "2026-01-01"
            raw.mkdir(parents=True)
            observations = {
                "observations": [
                    {
                        "date": "2024-01-01",
                        "realtime_start": "2024-02-01",
                        "realtime_end": "2024-02-29",
                        "value": "1.0",
                    },
                    {
                        "date": "2025-01-01",
                        "realtime_start": "2025-02-01",
                        "realtime_end": "2025-02-28",
                        "value": "2.0",
                    },
                ]
            }
            for series_id in FRED_SERIES:
                (raw / f"{series_id}.json").write_text(json.dumps(observations), encoding="utf-8")
            result = build_alfred_initial_release_features(root, "2026-01-01")
            self.assertEqual(result["vintage_status"], "initial_release_only")
            self.assertTrue(
                (
                    root / "processed" / "2026-01-01-alfred-initial" / "macro_monthly.parquet"
                ).is_file()
            )

    def test_alfred_key_is_validated_before_network_use(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            download_alfred_initial_releases(Path(directory), "2026-01-01", "not-a-key")


if __name__ == "__main__":
    unittest.main(verbosity=2)
