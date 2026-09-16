"""Pure-Python command-line interface for local development workflows."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .ingestion import (
    build_alfred_initial_release_features,
    build_fannie_parquet,
    build_monthly_macro_features,
    build_release_manifest,
    download_alfred_initial_releases,
    download_fred_snapshot,
    write_manifest,
)
from .models import fit_fannie_discrete_time_hazard, fit_segment_pd_benchmark
from .paths import fannie_data_root, fannie_release_directory, macro_data_root
from .publishing import publish_docx
from .validation import compare_pd_candidates

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


def _fit_pd_hazard(arguments: argparse.Namespace) -> int:
    import json
    from datetime import date

    root = fannie_data_root()
    data = root / "processed" / arguments.release / arguments.dataset_version
    report = fit_fannie_discrete_time_hazard(
        data / "fannie_monthly.parquet",
        data / "fannie_annual_dscr.parquet",
        root / "artifacts" / arguments.release / arguments.model_version,
        train_end=date.fromisoformat(arguments.train_end),
        validation_end=date.fromisoformat(arguments.validation_end),
        negative_sample_rate=arguments.negative_sample_rate,
    )
    print(json.dumps(report, indent=2))
    return 0


def _download_macro(arguments: argparse.Namespace) -> int:
    import json

    print(json.dumps(download_fred_snapshot(macro_data_root(), arguments.snapshot_date), indent=2))
    return 0


def _build_macro(arguments: argparse.Namespace) -> int:
    import json

    print(
        json.dumps(
            build_monthly_macro_features(macro_data_root(), arguments.snapshot_date), indent=2
        )
    )
    return 0


def _download_alfred(arguments: argparse.Namespace) -> int:
    import json

    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Set FRED_API_KEY before downloading ALFRED vintages")
    report = download_alfred_initial_releases(macro_data_root(), arguments.snapshot_date, api_key)
    print(json.dumps(report, indent=2))
    return 0


def _build_alfred(arguments: argparse.Namespace) -> int:
    import json

    report = build_alfred_initial_release_features(macro_data_root(), arguments.snapshot_date)
    print(json.dumps(report, indent=2))
    return 0


def _fit_pd_macro(arguments: argparse.Namespace) -> int:
    import json
    from datetime import date

    root = fannie_data_root()
    data = root / "processed" / arguments.release / arguments.dataset_version
    macro = macro_data_root() / "processed" / arguments.snapshot_date / "macro_monthly.parquet"
    report = fit_fannie_discrete_time_hazard(
        data / "fannie_monthly.parquet",
        data / "fannie_annual_dscr.parquet",
        root / "artifacts" / arguments.release / arguments.model_version,
        train_end=date.fromisoformat(arguments.train_end),
        validation_end=date.fromisoformat(arguments.validation_end),
        negative_sample_rate=arguments.negative_sample_rate,
        macro_parquet=macro,
        macro_features=tuple(arguments.macro_features.split(",")),
        model_version="0.2.0-development-macro",
    )
    print(json.dumps(report, indent=2))
    return 0


def _fit_pd_vintage(arguments: argparse.Namespace) -> int:
    import json
    from datetime import date

    root = fannie_data_root()
    data = root / "processed" / arguments.release / arguments.dataset_version
    macro = (
        macro_data_root()
        / "processed"
        / f"{arguments.snapshot_date}-alfred-initial"
        / "macro_monthly.parquet"
    )
    report = fit_fannie_discrete_time_hazard(
        data / "fannie_monthly.parquet",
        data / "fannie_annual_dscr.parquet",
        root / "artifacts" / arguments.release / arguments.model_version,
        train_end=date.fromisoformat(arguments.train_end),
        validation_end=date.fromisoformat(arguments.validation_end),
        negative_sample_rate=arguments.negative_sample_rate,
        macro_parquet=macro,
        macro_features=("unemployment_rate", "unemployment_change_12m"),
        model_version="0.3.0-development-initial-release",
    )
    print(json.dumps(report, indent=2))
    return 0


def _compare_pd(arguments: argparse.Namespace) -> int:
    import json

    root = fannie_data_root()
    report = compare_pd_candidates(
        root / "artifacts" / arguments.release,
        root / "comparisons" / arguments.release / arguments.comparison_version,
    )
    print(json.dumps(report["assessment"], indent=2))
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

    hazard = commands.add_parser("fit-fannie-pd-hazard", help="fit classical logistic hazard")
    hazard.add_argument("--release", required=True)
    hazard.add_argument("--dataset-version", default="v0.3.0")
    hazard.add_argument("--model-version", default="pd-hazard-v0.1.1")
    hazard.add_argument("--train-end", default="2018-12-31")
    hazard.add_argument("--validation-end", default="2022-12-31")
    hazard.add_argument("--negative-sample-rate", type=float, default=0.10)
    hazard.set_defaults(handler=_fit_pd_hazard)

    macro_download = commands.add_parser(
        "download-macro", help="download an immutable FRED snapshot"
    )
    macro_download.add_argument("--snapshot-date", required=True)
    macro_download.set_defaults(handler=_download_macro)

    macro_build = commands.add_parser("build-macro", help="build lagged monthly macro features")
    macro_build.add_argument("--snapshot-date", required=True)
    macro_build.set_defaults(handler=_build_macro)

    alfred_download = commands.add_parser(
        "download-alfred", help="download initial-release macro vintages"
    )
    alfred_download.add_argument("--snapshot-date", required=True)
    alfred_download.set_defaults(handler=_download_alfred)

    alfred_build = commands.add_parser(
        "build-alfred", help="build initial-release monthly macro features"
    )
    alfred_build.add_argument("--snapshot-date", required=True)
    alfred_build.set_defaults(handler=_build_alfred)

    macro_model = commands.add_parser("fit-fannie-pd-macro", help="fit hazard with macro features")
    macro_model.add_argument("--release", required=True)
    macro_model.add_argument("--snapshot-date", required=True)
    macro_model.add_argument("--dataset-version", default="v0.3.0")
    macro_model.add_argument("--model-version", default="pd-hazard-macro-v0.2.0")
    macro_model.add_argument("--train-end", default="2018-12-31")
    macro_model.add_argument("--validation-end", default="2022-12-31")
    macro_model.add_argument("--negative-sample-rate", type=float, default=0.10)
    macro_model.add_argument(
        "--macro-features",
        default=(
            "unemployment_rate,unemployment_change_12m,financial_conditions,"
            "treasury_10y,baa_treasury_spread,rental_vacancy_rate,rent_cpi_yoy"
        ),
    )
    macro_model.set_defaults(handler=_fit_pd_macro)

    vintage_model = commands.add_parser(
        "fit-fannie-pd-vintage", help="fit labor challenger with initial-release vintages"
    )
    vintage_model.add_argument("--release", required=True)
    vintage_model.add_argument("--snapshot-date", required=True)
    vintage_model.add_argument("--dataset-version", default="v0.3.0")
    vintage_model.add_argument("--model-version", default="pd-hazard-alfred-v0.3.0")
    vintage_model.add_argument("--train-end", default="2018-12-31")
    vintage_model.add_argument("--validation-end", default="2022-12-31")
    vintage_model.add_argument("--negative-sample-rate", type=float, default=0.10)
    vintage_model.set_defaults(handler=_fit_pd_vintage)

    comparison = commands.add_parser(
        "compare-fannie-pd", help="compare baseline, revised-macro, and vintage PD candidates"
    )
    comparison.add_argument("--release", required=True)
    comparison.add_argument("--comparison-version", default="pd-comparison-v0.1.0")
    comparison.set_defaults(handler=_compare_pd)
    return result


def main() -> int:
    """Run the selected command."""
    arguments = parser().parse_args()
    return int(arguments.handler(arguments))


if __name__ == "__main__":
    raise SystemExit(main())
