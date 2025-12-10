import pandas as pd

from datavalgen.safevalidate import safe_validate_dataframe
from .test_validate import SimpleModel


def test_safe_validate_dataframe():
    df = pd.DataFrame(
        [
            {"id": -1, "age": 200, "birthday": "not-a-date"},
        ]
    )

    error_count = safe_validate_dataframe(df, SimpleModel)

    # check return type
    assert isinstance(error_count, int)
    # we expect 3 errors: one per field
    assert error_count == 3


def test_safe_validate_dataframe_multiple():
    df = pd.DataFrame(
        [
            {"id": -1, "age": 200, "birthday": "not-a-date"},
            {"id": 1, "age": 20, "birthday": "1990-01-01"},
        ]
    )

    error_count = safe_validate_dataframe(df, SimpleModel)

    # check return type
    assert isinstance(error_count, int)
    # we expect 3 errors: one per field
    assert error_count == 3


def test_safe_validate_dataframe_valid():
    df = pd.DataFrame(
        [
            {"id": 1, "age": 20, "birthday": "1990-01-01"},
            {"id": 3, "age": 21, "birthday": "1990-01-02"},
            {"id": 6, "age": 22, "birthday": "1990-02-01"},
        ]
    )

    error_count = safe_validate_dataframe(df, SimpleModel)

    # check return type
    assert isinstance(error_count, int)
    # we expect 3 errors: one per field
    assert error_count == 0
