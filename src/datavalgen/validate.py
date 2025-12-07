from typing import List

import pandas as pd
from pydantic import BaseModel, TypeAdapter
from pydantic_core import ErrorDetails, ValidationError


def validate_dataframe(
    df: pd.DataFrame, model: type[BaseModel]
) -> list[ErrorDetails] | int:
    """
    Validate each row of a DataFrame against a Pydantic model.

    Each row in `df` is converted to a dict and validated using a
    `TypeAdapter` for `list[model]`, so the whole DataFrame is treated
    as a list of model instances.

    Args:
        df: The pandas DataFrame to validate (one row per model instance).
        model: The Pydantic BaseModel subclass used for validation.

    Returns:
        list[ErrorDetails]: Detailed validation errors when `no_details` is False.
            (Empty list means no errors.)

    Notes:
        Validation errors are caught and returned; no exception is raised.
    """
    errors = []
    adapter = TypeAdapter(list[model])
    try:
        adapter.validate_python(df.to_dict("records"))
    except ValidationError as e:
        errors = e.errors(include_url=False)

    return errors


def validate_column_names(df: pd.DataFrame, model: type[BaseModel]) -> List[str]:
    """
    Compare DataFrame columns to the model's field names and report mismatches.

    Args:
        df: The pandas DataFrame to check.
        model: The Pydantic BaseModel subclass whose `model_fields` define
            the expected column names.

    Returns:
        List[str]: Human-readable messages describing missing or extra columns.
        Returns an empty list if columns match exactly.
    """
    expected = set(model.model_fields.keys())
    actual = set(df.columns)

    missing = expected - actual
    extra = actual - expected

    error_lines = []

    if missing or extra:
        if missing:
            error_lines.append(f"Missing expected columns: {missing}")
        if extra:
            error_lines.append(f"Unexpected columns: {extra}")

    return error_lines
