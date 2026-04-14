import json
import importlib

import pytest

from datavalgen.safe_validate import safe_validate
from datavalgen.validate import check_csv_file
from .test_validate import SimpleModel


def test_check_csv_file_error_count(tmp_path):
    csv_path = tmp_path / "data.csv"
    _write_text(csv_path, "id,age,birthday\n-1,200,not-a-date\n")

    error_count = check_csv_file(csv_path, SimpleModel).num_errors

    assert isinstance(error_count, int)
    assert error_count == 3


def test_check_csv_file_error_count_multiple(tmp_path):
    csv_path = tmp_path / "data.csv"
    _write_text(
        csv_path,
        "id,age,birthday\n-1,200,not-a-date\n1,20,1990-01-01\n",
    )

    error_count = check_csv_file(csv_path, SimpleModel).num_errors

    assert isinstance(error_count, int)
    assert error_count == 3


def test_check_csv_file_error_count_valid(tmp_path):
    csv_path = tmp_path / "data.csv"
    _write_text(
        csv_path,
        "id,age,birthday\n1,20,1990-01-01\n3,21,1990-01-02\n6,22,1990-02-01\n",
    )

    error_count = check_csv_file(csv_path, SimpleModel).num_errors

    assert isinstance(error_count, int)
    assert error_count == 0


def _write_text(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_safe_validate_writes_json_count(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    out_path = tmp_path / "out.json"
    _write_text(csv_path, "id,age,birthday\n-1,200,not-a-date\n")
    monkeypatch.setenv("DATAVALGEN_DISTRIBUTION", "example-dist")

    safe_validate_module = importlib.import_module("datavalgen.safe_validate")
    monkeypatch.setattr(
        safe_validate_module,
        "get_model",
        lambda _, distribution=None: SimpleModel,
    )
    safe_validate(
        dataset_path=csv_path,
        output_path=out_path,
        pydantic_model_name="simple",
    )

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload == {"num_errors": 3}


def test_safe_validate_ignores_extra_columns(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    out_path = tmp_path / "out.json"
    _write_text(csv_path, "id,age,birthday,extra\n-1,200,not-a-date,ignored\n")
    monkeypatch.setenv("DATAVALGEN_DISTRIBUTION", "example-dist")

    safe_validate_module = importlib.import_module("datavalgen.safe_validate")
    monkeypatch.setattr(
        safe_validate_module,
        "get_model",
        lambda _, distribution=None: SimpleModel,
    )
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
    monkeypatch.setenv("DATAVALGEN_DISTRIBUTION", "example-dist")
    safe_validate_module = importlib.import_module("datavalgen.safe_validate")
    monkeypatch.setattr(
        safe_validate_module,
        "get_model",
        lambda _, distribution=None: SimpleModel,
    )
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
    monkeypatch.setenv("DATAVALGEN_DISTRIBUTION", "example-dist")

    with pytest.raises(
        ValueError,
        match="pydantic_model_name was not provided and DATAVALGEN_MODEL is not set",
    ):
        safe_validate(
            dataset_path=csv_path,
            output_path=out_path,
            pydantic_model_name=None,
        )


def test_safe_validate_errors_without_distribution_env(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    out_path = tmp_path / "out.json"
    _write_text(csv_path, "id,age,birthday\n-1,200,not-a-date\n")

    monkeypatch.delenv("DATAVALGEN_DISTRIBUTION", raising=False)

    with pytest.raises(
        ValueError,
        match="DATAVALGEN_DISTRIBUTION must be set for safe_validate",
    ):
        safe_validate(
            dataset_path=csv_path,
            output_path=out_path,
            pydantic_model_name="simple",
        )
