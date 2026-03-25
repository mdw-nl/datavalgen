import json
import importlib

import pandas as pd
import pytest

from datavalgen.safe_validate import safe_validate
from datavalgen.validate import check_dataframe
from .test_validate import SimpleModel


def test_check_dataframe_error_count():
    df = pd.DataFrame(
        [
            {"id": -1, "age": 200, "birthday": "not-a-date"},
        ]
    )

    error_count = len(check_dataframe(df, SimpleModel).errors)

    # check return type
    assert isinstance(error_count, int)
    # we expect 3 errors: one per field
    assert error_count == 3


def test_check_dataframe_error_count_multiple():
    df = pd.DataFrame(
        [
            {"id": -1, "age": 200, "birthday": "not-a-date"},
            {"id": 1, "age": 20, "birthday": "1990-01-01"},
        ]
    )

    error_count = len(check_dataframe(df, SimpleModel).errors)

    # check return type
    assert isinstance(error_count, int)
    # we expect 3 errors: one per field
    assert error_count == 3


def test_check_dataframe_error_count_valid():
    df = pd.DataFrame(
        [
            {"id": 1, "age": 20, "birthday": "1990-01-01"},
            {"id": 3, "age": 21, "birthday": "1990-01-02"},
            {"id": 6, "age": 22, "birthday": "1990-02-01"},
        ]
    )

    error_count = len(check_dataframe(df, SimpleModel).errors)

    # check return type
    assert isinstance(error_count, int)
    # we expect 3 errors: one per field
    assert error_count == 0


def _write_text(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_safe_validate_writes_json_count(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    out_path = tmp_path / "out.json"
    _write_text(csv_path, "id,age,birthday\n-1,200,not-a-date\n")

    safe_validate_module = importlib.import_module("datavalgen.safe_validate")
    monkeypatch.setattr(safe_validate_module, "get_model", lambda _: SimpleModel)
    safe_validate(
        dataset_path=csv_path,
        output_path=out_path,
        pydantic_model_name="simple",
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload == {"num_errors": 3}


def test_safe_validate_uses_datavalgen_model_env_fallback(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    out_path = tmp_path / "out.json"
    _write_text(csv_path, "id,age,birthday\n-1,200,not-a-date\n")

    monkeypatch.setenv("DATAVALGEN_MODEL", "simple")
    safe_validate_module = importlib.import_module("datavalgen.safe_validate")
    monkeypatch.setattr(safe_validate_module, "get_model", lambda _: SimpleModel)
    safe_validate(
        dataset_path=csv_path,
        output_path=out_path,
        pydantic_model_name=None,
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload == {"num_errors": 3}


def test_safe_validate_errors_without_named_or_env_model(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    out_path = tmp_path / "out.json"
    _write_text(csv_path, "id,age,birthday\n-1,200,not-a-date\n")

    monkeypatch.delenv("DATAVALGEN_MODEL", raising=False)

    with pytest.raises(
        ValueError,
        match="pydantic_model_name was not provided and DATAVALGEN_MODEL is not set",
    ):
        safe_validate(
            dataset_path=csv_path,
            output_path=out_path,
            pydantic_model_name=None,
        )
