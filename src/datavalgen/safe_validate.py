"""
Safe validation functions that avoid potentially returning sensitive data.
"""

import pandas as pd
from pydantic import BaseModel
from .validate import validate_dataframe

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
