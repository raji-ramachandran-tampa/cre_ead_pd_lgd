import csv
import json
import tempfile
import unittest
from pathlib import Path

from cre_expected_loss.validation import compare_pd_candidates


class PDCandidateComparisonTest(unittest.TestCase):
    def _candidate(self, root: Path, name: str, auc: float, oe: float) -> None:
        directory = root / name
        directory.mkdir()
        metrics = {
            sample: {
                "sample_rows": rows,
                "weighted_observations": float(rows * 10),
                "weighted_events": float(events),
                "weighted_predicted_events": float(events / oe),
                "observed_to_expected": oe,
                "roc_auc": auc,
                "average_precision": 0.01,
                "brier_score": 0.001,
                "log_loss": 0.002,
            }
            for sample, rows, events in (
                ("train", 100, 10),
                ("validation", 50, 2),
                ("test", 40, 3),
            )
        }
        report = {
            "train_end": "2018-12-31",
            "validation_end": "2022-12-31",
            "metrics": metrics,
        }
        (directory / "model_report.json").write_text(json.dumps(report), encoding="utf-8")
        with (directory / "coefficients.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["transformed_feature", "log_odds_coefficient"])
            writer.writerow(["numeric__ltv", 0.5])

    def test_writes_controlled_comparison_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts, output = root / "artifacts", root / "output"
            artifacts.mkdir()
            candidates = {"baseline": "a", "revised_macro": "b", "vintage_macro": "c"}
            self._candidate(artifacts, "a", 0.70, 0.8)
            self._candidate(artifacts, "b", 0.75, 1.2)
            self._candidate(artifacts, "c", 0.80, 1.1)

            result = compare_pd_candidates(artifacts, output, candidates)

            self.assertEqual(result["assessment"]["test_discrimination_leader"], "vintage_macro")
            self.assertEqual(result["status"], "development_evidence_proposed_not_approved")
            self.assertTrue((output / "comparison.json").is_file())
            self.assertTrue((output / "metrics.csv").is_file())
            self.assertTrue((output / "comparison.md").is_file())
            with self.assertRaises(FileExistsError):
                compare_pd_candidates(artifacts, output, candidates)

    def test_rejects_incomparable_cutoffs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            candidates = {"baseline": "a", "revised_macro": "b", "vintage_macro": "c"}
            for name in ("a", "b", "c"):
                self._candidate(artifacts, name, 0.7, 1.0)
            report_path = artifacts / "c" / "model_report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["train_end"] = "2019-12-31"
            report_path.write_text(json.dumps(report), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "chronological cutoffs"):
                compare_pd_candidates(artifacts, root / "output", candidates)


if __name__ == "__main__":
    unittest.main()
