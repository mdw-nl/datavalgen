import pandas as pd
from pydantic import BaseModel, TypeAdapter
from pydantic_core import ErrorDetails, ValidationError

from datavalgen.check_result import CheckResult


def select_model_columns(
    df: pd.DataFrame, model: type[BaseModel]
) -> pd.DataFrame:
    """
    Return the subset of DataFrame columns defined by the model.

    This lets callers validate a selected model against a wider CSV while
    ignoring unrelated extra columns.
    """
    return df[list(model.model_fields.keys())]


def check_dataframe(
    df: pd.DataFrame, model: type[BaseModel]
) -> CheckResult[ErrorDetails]:
    """
    Validate each row of a DataFrame against a Pydantic model.

    Each row in `df` is converted to a dict and validated using a
    `TypeAdapter` for `list[model]`, so the whole DataFrame is treated
    as a list of model instances.

    Args:
        df: The pandas DataFrame to validate (one row per model instance).
        model: The Pydantic BaseModel subclass used for validation.

    Returns:
        CheckResult[ErrorDetails]: Detailed validation errors in `errors`.
            The result is `ok` when no validation errors were found.

    Notes:
        Validation errors are caught and returned; no exception is raised.
    """
    errors: tuple[ErrorDetails, ...] = ()
    # Ignore unrelated extra columns so subset models can validate against
    # wider CSVs once required model columns are present.
    df = select_model_columns(df, model)
    adapter = TypeAdapter(list[model])
    try:
        adapter.validate_python(df.to_dict("records"))
    except ValidationError as e:
        errors = tuple(e.errors(include_url=False))

    return CheckResult(errors=errors)


def check_column_names(
    df: pd.DataFrame, model: type[BaseModel]
) -> CheckResult[str]:
    """
    Compare DataFrame columns to the model's field names and report mismatches.

    Args:
        df: The pandas DataFrame to check.
        model: The Pydantic BaseModel subclass whose `model_fields` define
            the expected column names.

    Returns:
        CheckResult[str]: Human-readable messages describing missing or extra
            columns. Missing columns are returned in `errors`; extra columns are
            returned in `warnings`. The result is `ok` when there are no errors.
    """
    expected = set(model.model_fields.keys())
    actual = set(df.columns)

    missing = expected - actual
    extra = actual - expected

    error_lines: list[str] = []
    warning_lines: list[str] = []

    if missing:
        error_lines.append(f"Missing expected columns: {missing}")
    if extra:
        warning_lines.append(f"Unexpected columns: {extra}")

    return CheckResult(
        errors=tuple(error_lines),
        warnings=tuple(warning_lines),
    )
