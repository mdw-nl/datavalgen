from datetime import date

import pandas as pd
from pydantic import BaseModel, Field

from datavalgen.validate import validate_column_names, validate_dataframe


class SimpleModel(BaseModel):
    id: int = Field(..., gt=0)
    age: int = Field(..., ge=0, le=120)
    birthday: date


def test_validate_column_names_ok():
    df = pd.DataFrame(columns=["id", "age", "birthday"])
    errors = validate_column_names(df, SimpleModel)
    assert errors == []


def test_validate_column_names_mismatch():
    df = pd.DataFrame(columns=["id", "wrong"])
    errors = validate_column_names(df, SimpleModel)

    # Two lines: missing + unexpected
    assert len(errors) == 2
    assert "Missing expected columns" in errors[0]
    assert "'age'" in errors[0]
    assert "'birthday'" in errors[0]
    assert "Unexpected columns" in errors[1]
    assert "'wrong'" in errors[1]


def test_validate_dataframe_ok_count_only():
    df = pd.DataFrame([{"id": 1, "age": 30, "birthday": "1990-01-01"}])
    count = validate_dataframe(df, SimpleModel)
    assert count == []


def test_validate_dataframe_errors():
    df = pd.DataFrame(
        [
            {"id": -1, "age": 200, "birthday": "not-a-date"},
        ]
    )

    errors = validate_dataframe(df, SimpleModel)

    # check return type
    assert isinstance(errors, list)
    # shouln't be empty
    assert errors
    # we expect 3 errors: one per field
    assert len(errors) == 3
