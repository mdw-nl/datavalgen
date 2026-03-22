import json

import pytest

from datavalgen.safe_validate_run_context import safe_validate

from .test_validate import SimpleModel


def _write_text(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_safe_validate_writes_json_count(tmp_path, monkeypatch):
    csv_path = tmp_path / "data.csv"
    out_path = tmp_path / "out.json"
    _write_text(csv_path, "id,age,birthday\n-1,200,not-a-date\n")

    monkeypatch.setattr(
        "datavalgen.safe_validate_run_context.get_model", lambda _: SimpleModel
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
    monkeypatch.setattr(
        "datavalgen.safe_validate_run_context.get_model", lambda _: SimpleModel
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

    with pytest.raises(
        ValueError,
        match="pydantic_model_name was not provided and DATAVALGEN_MODEL is not set",
    ):
        safe_validate(
            dataset_path=csv_path,
            output_path=out_path,
            pydantic_model_name=None,
        )
