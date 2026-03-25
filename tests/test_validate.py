from datetime import date

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from datavalgen.check_result import CheckResult
from datavalgen.validate import check_column_names, check_dataframe, select_model_columns


class SimpleModel(BaseModel):
    id: int = Field(..., gt=0)
    age: int = Field(..., ge=0, le=120)
    birthday: date


class StrictSimpleModel(SimpleModel):
    model_config = ConfigDict(extra="forbid")


def test_check_column_names_ok():
    df = pd.DataFrame(columns=["id", "age", "birthday"])
    result = check_column_names(df, SimpleModel)
    assert result.errors == ()
    assert result.warnings == ()
    assert result.ok is True


def test_check_column_names_missing_and_extra():
    df = pd.DataFrame(columns=["id", "wrong"])
    result = check_column_names(df, SimpleModel)

    assert len(result.errors) == 1
    assert "Missing expected columns" in result.errors[0]
    assert "'age'" in result.errors[0]
    assert "'birthday'" in result.errors[0]
    assert len(result.warnings) == 1
    assert "Unexpected columns" in result.warnings[0]
    assert "'wrong'" in result.warnings[0]


def test_check_column_names_extra_only_is_warning():
    df = pd.DataFrame(columns=["id", "age", "birthday", "extra"])
    result = check_column_names(df, SimpleModel)

    assert result.errors == ()
    assert len(result.warnings) == 1
    assert "Unexpected columns" in result.warnings[0]
    assert "'extra'" in result.warnings[0]
    assert result.ok is True


def test_check_dataframe_ok_count_only():
    df = pd.DataFrame([{"id": 1, "age": 30, "birthday": "1990-01-01"}])
    result = check_dataframe(df, SimpleModel)
    assert result.errors == ()
    assert result.ok is True


def test_check_dataframe_errors():
    df = pd.DataFrame(
        [
            {"id": -1, "age": 200, "birthday": "not-a-date"},
        ]
    )

    result = check_dataframe(df, SimpleModel)

    # check return type
    assert isinstance(result, CheckResult)
    # shouln't be empty
    assert result.errors
    # we expect 3 errors: one per field
    assert len(result.errors) == 3


def test_select_model_columns_drops_extra_columns():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "age": 30,
                "birthday": "1990-01-01",
                "extra": "ignored",
            }
        ]
    )

    selected = select_model_columns(df, SimpleModel)

    assert list(selected.columns) == ["id", "age", "birthday"]


def test_check_dataframe_ignores_extra_columns_for_strict_models():
    df = pd.DataFrame(
        [
            {
                "id": 1,
                "age": 30,
                "birthday": "1990-01-01",
                "extra": "ignored",
            }
        ]
    )

    result = check_dataframe(df, StrictSimpleModel)

    assert result.errors == ()
    assert result.ok is True


def test_check_result_ok_property():
    assert CheckResult[str]().ok is True
    assert CheckResult[str](warnings=("warning",)).ok is True
    assert CheckResult[str](errors=("error",)).ok is False


def test_check_column_names_returns_common_shape():
    df = pd.DataFrame(columns=["id", "wrong"])
    result = check_column_names(df, SimpleModel)

    assert isinstance(result, CheckResult)
    assert result.ok is False
    assert len(result.errors) == 1
    assert len(result.warnings) == 1


def test_check_dataframe_returns_common_shape():
    df = pd.DataFrame(
        [
            {"id": -1, "age": 200, "birthday": "not-a-date"},
        ]
    )

    result = check_dataframe(df, SimpleModel)

    assert isinstance(result, CheckResult)
    assert result.ok is False
    assert result.warnings == ()
    assert len(result.errors) == 3
