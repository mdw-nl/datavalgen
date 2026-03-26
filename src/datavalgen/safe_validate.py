"""
Safe validation functions that avoid potentially returning sensitive data.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from run_context import run_context

from datavalgen.plugins import get_model
from datavalgen.read_csv import read_csv_raw
from datavalgen.validate import check_column_names, check_dataframe


@run_context(
    input_uris="dataset_path",
    named_arguments="pydantic_model_name",
    output_uris="output_path",
)
def safe_validate(
    dataset_path: Path,
    output_path: Path,
    pydantic_model_name: str | None = None,
    json_out: bool = True,
) -> None:
    """
    Validate one CSV and write privacy-safe result to output path.
    """
    model_name = pydantic_model_name or os.environ.get("DATAVALGEN_MODEL")
    if not model_name:
        raise ValueError(
            "pydantic_model_name was not provided and DATAVALGEN_MODEL is not set"
        )

    # In privacy-sensitive FL use, we may let the caller choose among multiple
    # models, but only from the distribution the image author explicitly trusts.
    distribution = os.environ.get("DATAVALGEN_DISTRIBUTION")
    if not distribution:
        raise ValueError(
            "DATAVALGEN_DISTRIBUTION must be set for safe_validate so model "
            "lookup is restricted to one trusted distribution"
        )
    model = get_model(model_name, distribution=distribution)
    df = read_csv_raw(dataset_path)

    column_check = check_column_names(df, model)
    if column_check.errors:
        num_errors = len(column_check.errors)
    else:
        num_errors = len(check_dataframe(df, model).errors)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if json_out:
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump({"num_errors": int(num_errors)}, fp)
            fp.write("\n")
    else:
        with open(output_path, "w", encoding="utf-8") as fp:
            fp.write(f"{int(num_errors)}\n")
