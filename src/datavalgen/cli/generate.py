from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from datavalgen.cli.utils.print import print_factory_list
from datavalgen.factory import BaseDataModelFactory
from datavalgen.plugins import get_factory
from datavalgen.cli.utils.docker import (
    docker_detect_missing_volume,
    docker_fix_permissions,
)
from pandas import DataFrame

__all__: list[str] = ["main"]


def parse_args(argv) -> Any:
    default_datafactory: str | None = os.environ.get("DATAVALGEN_FACTORY")

    p = argparse.ArgumentParser(
        prog="datavalgen generate",
        description="Generate fake data rows from a data factory (datavalgen factory)",
    )
    p.add_argument(
        "-l",
        "--list",
        help="List available factories and exit",
        action="store_true",
    )
    p.add_argument(
        "-f",
        "--factory",
        default=default_datafactory,
        help="Name of the factory (pydantic, polyfactory) to use, as registered in the entry point group 'datavalgen.factories'",
    )
    p.add_argument(
        "-n", "--num-rows", type=int, default=10, help="Rows to generate (default: 10)"
    )
    out: argparse._MutuallyExclusiveGroup = p.add_mutually_exclusive_group()
    out.add_argument(
        "-o", "--output", type=Path, help="Write to this file (format via --format)"
    )
    out.add_argument(
        "--show-df", action="store_true", help="Print DataFrame to stdout instead"
    )
    p.add_argument(
        "--force", action="store_true", help="Overwrite existing output file"
    )
    p.add_argument(
        "--format",
        choices=["csv", "parquet"],
        default="csv",
        help="Output format if -o is given (default: csv)",
    )
    p.add_argument("--columns", help="Comma-separated subset of columns to keep")
    p.add_argument(
        "-r",
        "--replace",
        action="append",
        metavar="COL=VAL",
        help="Set every entry in COL to VAL. Repeat or comma-separate.",
    )

    args: argparse.Namespace = p.parse_args(argv)

    # handle --list early, just list factories
    if args.list:
        return args

    if args.factory is None:
        p.error(
            "Please provide a valid -f/--factory argument or set the "
            "DATAVALGEN_FACTORY environment variable."
        )

    if not args.output and not args.show_df:
        p.error("Please provide either -o/--output or --show-df.")

    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.list:
        print_factory_list()
        sys.exit(0)

    factory: BaseDataModelFactory = get_factory(args.factory)

    df: DataFrame = factory.batch_dataframe(args.num_rows)

    # TODO: this replace option was a quick last-minute addition since fake
    # data generation is very rudimentary. Improve & remove this?
    if args.replace:
        replacements: dict[str, str] = {}
        for spec in args.replace:
            # may be ["a=1,b=2", "c=foo"] etc.
            for pair in spec.split(","):
                # TODO: move this check to end of parse_args()
                if "=" not in pair:
                    sys.exit(f"Bad --replace syntax: {pair!r} (expected COL=VAL)")
                col, val = [s.strip() for s in pair.split("=", 1)]
                if col not in df.columns:
                    sys.exit(f"--replace: column {col!r} not in DataFrame")
                replacements[col] = val

        for col, val in replacements.items():
            df[col] = val

    # optional column filter
    if args.columns:
        cols: list[Any] = [c.strip() for c in args.columns.split(",")]
        missing: set[Any] = set(cols) - set(df.columns)
        if missing:
            sys.exit(f"Columns not in model: {', '.join(missing)}")
        df = df[cols]

    if args.show_df:
        print(df)
        return

    out_path: Path = args.output
    if out_path.exists() and not args.force:
        sys.exit(f"{out_path} exists. Use --force to overwrite.")

    out_path = out_path.resolve()

    # when run via `docker`, documented way is to write out to `/data` dir
    # but user might've forgotten to mount a volume there
    if docker_detect_missing_volume(out_path):
        sys.exit(1)

    if args.format == "csv":
        df.to_csv(out_path, index=False)
    else:
        try:
            df.to_parquet(out_path, index=False)
        except ImportError:
            sys.exit("Parquet output needs 'pyarrow'.")

    docker_fix_permissions(out_path)

    print(f"Generated {args.num_rows} rows to {out_path} in {args.format} format.")
