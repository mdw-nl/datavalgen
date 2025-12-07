from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, List

from datavalgen.cli.utils.print import print_model_list
from pydantic import BaseModel
from datavalgen.plugins import get_model

from datavalgen.readcsv import read_csv_raw
from datavalgen.reporterrors import format_val_errors
from datavalgen.validate import validate_column_names, validate_dataframe


from pandas import DataFrame

__all__: list[str] = ["main"]


def find_default_csv_path() -> Path | None:
    candidate: Path | None = None
    if "DATAVALGEN_DATA" in os.environ:
        candidate = Path(os.environ["DATAVALGEN_DATA"])
        if candidate.is_file():
            return candidate
    candidate = Path("/data.csv")
    if candidate.is_file():
        return candidate


def parse_args(argv) -> Any:
    default_model: str | None = os.environ.get("DATAVALGEN_MODEL")

    p = argparse.ArgumentParser(
        prog="datavalgen validate",
        description="Validate a CSV against a Pydantic schema",
    )
    p.add_argument(
        "-m",
        "--model",
        default=default_model,
        help="Model name (pydantic) as registed in the entry point group 'datavalgen.models'",
    )
    p.add_argument(
        "-d",
        "--data",
        default=find_default_csv_path(),
        type=Path,
        help="Path to the CSV you want to check",
    )
    p.add_argument(
        "--max-errors",
        type=int,
        default=10,
        help="How many individual cell errors to show (default: 10)",
    )
    p.add_argument(
        "-l",
        "--list",
        help="List available models and exit",
        action="store_true",
    )

    args: argparse.Namespace = p.parse_args(argv)

    if args.model is None and not args.list:
        print(
            "Error: -m/--model is required (or set DATAVALGEN_MODEL env var)",
            file=sys.stderr,
        )
        sys.exit(2)
    if args.data is None and not args.list:
        print(
            "Error: -d/--data is required, or set DATAVALGEN_DATA env var,"
            " or place a file at /data.csv",
            file=sys.stderr,
        )
        sys.exit(2)

    return args


def main(argv: list[str] | None = None) -> None:
    """Entry-point for `datavalgen validate ...`."""
    args = parse_args(argv)

    if args.list:
        print_model_list()
        sys.exit(0)

    model: BaseModel = get_model(args.model)

    df: DataFrame = read_csv_raw(args.data)

    errors: List[str] = validate_column_names(df, model)
    if errors:
        print(
            "❌ Column names do not match the schema. Stopping any further validation."
        )
        print("\n".join(errors))
        sys.exit(1)

    errors = validate_dataframe(df, model)
    print(format_val_errors(errors, args.max_errors))

    if errors:
        print(
            f'⚠️  Note: errors above contain your actual data values ("Got: .."). Do not share.'
        )

    sys.exit(1 if errors else 0)
