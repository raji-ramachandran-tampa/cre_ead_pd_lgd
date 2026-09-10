"""Pure-Python command-line interface for local development workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .ingestion import build_fannie_parquet, build_release_manifest, write_manifest
from .models import fit_segment_pd_benchmark
from .paths import fannie_data_root, fannie_release_directory
from .publishing import publish_docx

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _test(_: argparse.Namespace) -> int:
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
        cwd=REPOSITORY_ROOT,
        check=False,
    ).returncode


def _data_root(arguments: argparse.Namespace) -> int:
    path = fannie_release_directory(arguments.release) if arguments.release else fannie_data_root()
    print(path)
    return 0


def _build_document(arguments: argparse.Namespace) -> int:
    directory = REPOSITORY_ROOT / "docs" / arguments.document
    source = directory / arguments.source
    defaults = directory / "pandoc.yaml"
    output = Path(arguments.output)
    if not output.is_absolute():
        output = directory / output
    print(publish_docx(source, output, defaults))
    return 0


def _intake_fannie(arguments: argparse.Namespace) -> int:
    release_directory = fannie_release_directory(arguments.release)
    manifest = build_release_manifest(
        release_directory,
        arguments.release,
        count_rows=arguments.count_rows,
    )
    if arguments.write_manifest:
        destination = fannie_data_root() / "manifests" / f"{arguments.release}_intake.json"
        print(write_manifest(manifest, destination))
    else:
        import json

        print(json.dumps(manifest, indent=2))
    return 0


def _build_fannie_dataset(arguments: argparse.Namespace) -> int:
    import json

    result = build_fannie_parquet(
        fannie_release_directory(arguments.release),
        fannie_data_root() / "processed" / arguments.release / arguments.dataset_version,
        arguments.release,
    )
    print(json.dumps(result["summary"], indent=2))
    return 0


def _fit_pd_benchmark(arguments: argparse.Namespace) -> int:
    import json
    from datetime import date

    root = fannie_data_root()
    report = fit_segment_pd_benchmark(
        root
        / "processed"
        / arguments.release
        / arguments.dataset_version
        / "fannie_monthly.parquet",
        root / "artifacts" / arguments.release / arguments.model_version,
        train_end=date.fromisoformat(arguments.train_end),
        validation_end=date.fromisoformat(arguments.validation_end),
        smoothing_observations=arguments.smoothing_observations,
    )
    print(json.dumps(report, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    """Create the command parser."""
    result = argparse.ArgumentParser(prog="cre-el")
    commands = result.add_subparsers(dest="command", required=True)

    tests = commands.add_parser("test", help="run the repository test suite")
    tests.set_defaults(handler=_test)

    data = commands.add_parser("data-root", help="show the configured Fannie data path")
    data.add_argument("--release", help="optional release such as 2026Q1")
    data.set_defaults(handler=_data_root)

    document = commands.add_parser("build-doc", help="publish a Markdown document to DOCX")
    document.add_argument(
        "--document",
        choices=("model_design", "model_development"),
        default="model_design",
    )
    document.add_argument("--source", default="content.md")
    document.add_argument("--output", default="preview.docx")
    document.set_defaults(handler=_build_document)

    intake = commands.add_parser("intake-fannie", help="inspect a Fannie MFLPD release")
    intake.add_argument("--release", required=True, help="release such as 2026Q1")
    intake.add_argument("--count-rows", action="store_true", help="stream and count all CSV rows")
    intake.add_argument(
        "--write-manifest",
        action="store_true",
        help="write an immutable manifest under the external data root",
    )
    intake.set_defaults(handler=_intake_fannie)

    dataset = commands.add_parser(
        "build-fannie-dataset", help="create typed modeling Parquet from a Fannie release"
    )
    dataset.add_argument("--release", required=True, help="release such as 2026Q1")
    dataset.add_argument("--dataset-version", default="v0.3.0")
    dataset.set_defaults(handler=_build_fannie_dataset)

    pd_model = commands.add_parser("fit-fannie-pd-benchmark", help="fit chronological PD benchmark")
    pd_model.add_argument("--release", required=True)
    pd_model.add_argument("--dataset-version", default="v0.3.0")
    pd_model.add_argument("--model-version", default="pd-benchmark-v0.1.0")
    pd_model.add_argument("--train-end", default="2018-12-31")
    pd_model.add_argument("--validation-end", default="2022-12-31")
    pd_model.add_argument("--smoothing-observations", type=float, default=500.0)
    pd_model.set_defaults(handler=_fit_pd_benchmark)
    return result


def main() -> int:
    """Run the selected command."""
    arguments = parser().parse_args()
    return int(arguments.handler(arguments))


if __name__ == "__main__":
    raise SystemExit(main())
