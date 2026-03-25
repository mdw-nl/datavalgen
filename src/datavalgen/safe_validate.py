"""
Safe validation functions that avoid potentially returning sensitive data.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
from pydantic import BaseModel
from run_context import run_context

from datavalgen.plugins import get_model
from datavalgen.read_csv import read_csv_raw
from datavalgen.validate import validate_column_names, validate_dataframe


def safe_validate_dataframe(
    df: pd.DataFrame, model: type[BaseModel]
) -> int:
    """
    Calls `validate_dataframe` and returns the count of validation errors.
    Args:
        df: The pandas DataFrame to validate.
        model: The Pydantic BaseModel subclass used for validation.
    Returns:
        int: The number of validation errors found in the DataFrame.
    """
    errors = len(validate_dataframe(df, model))

    # check errors is an integer at run-time
    if not isinstance(errors, int):
        raise TypeError("Expected integer count of errors")

    return errors


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

    model = get_model(model_name)
    df = read_csv_raw(dataset_path)

    column_name_errors = validate_column_names(df, model)
    if column_name_errors:
        num_errors = len(column_name_errors)
    else:
        num_errors = safe_validate_dataframe(df, model)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if json_out:
        with open(output_path, "w", encoding="utf-8") as fp:
            json.dump({"num_errors": int(num_errors)}, fp)
            fp.write("\n")
    else:
        with open(output_path, "w", encoding="utf-8") as fp:
            fp.write(f"{int(num_errors)}\n")
