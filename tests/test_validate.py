from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from datavalgen.check_result import CheckResult
from datavalgen.validate import check_column_names, check_csv_file


class SimpleModel(BaseModel):
    id: int = Field(..., gt=0)
    age: int = Field(..., ge=0, le=120)
    birthday: date


class StrictSimpleModel(SimpleModel):
    model_config = ConfigDict(extra="forbid")


def test_check_column_names_ok():
    result = check_column_names(("id", "age", "birthday"), SimpleModel)
    assert result.errors == ()
    assert result.warnings == ()
    assert result.ok is True


def test_check_column_names_missing_and_extra():
    result = check_column_names(("id", "wrong"), SimpleModel)

    assert isinstance(result, CheckResult)
    assert result.ok is False
    assert len(result.errors) == 1
    assert "Missing expected columns" in result.errors[0]
    assert "'age'" in result.errors[0]
    assert "'birthday'" in result.errors[0]
    assert len(result.warnings) == 1
    assert "Unexpected columns" in result.warnings[0]
    assert "'wrong'" in result.warnings[0]


def test_check_column_names_extra_only_is_warning():
    result = check_column_names(("id", "age", "birthday", "extra"), SimpleModel)

    assert result.errors == ()
    assert len(result.warnings) == 1
    assert "Unexpected columns" in result.warnings[0]
    assert "'extra'" in result.warnings[0]
    assert result.ok is True


def test_check_result_ok_property():
    assert CheckResult[str]().ok is True
    assert CheckResult[str](warnings=("warning",)).ok is True
    assert CheckResult[str](errors=("error",)).ok is False


def test_check_csv_file_ok(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "id,age,birthday\n1,30,1990-01-01\n2,20,1991-02-03\n",
        encoding="utf-8",
    )

    result = check_csv_file(csv_path, SimpleModel)

    assert result.ok is True
    assert result.num_errors == 0
    assert result.errors == ()
    assert result.warnings == ()


def test_check_csv_file_errors(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "id,age,birthday\n-1,200,not-a-date\n",
        encoding="utf-8",
    )

    result = check_csv_file(csv_path, SimpleModel)

    assert result.ok is False
    assert result.num_errors == 3
    assert len(result.errors) == 3


def test_check_csv_file_ignores_extra_columns_for_strict_models(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "id,age,birthday,extra\n1,30,1990-01-01,ignored\n",
        encoding="utf-8",
    )

    result = check_csv_file(csv_path, StrictSimpleModel)

    assert result.ok is True
    assert result.num_errors == 0
    assert len(result.warnings) == 1
    assert "Unexpected columns" in result.warnings[0]


def test_check_csv_file_uses_column_names_not_csv_order(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "age,id,birthday\n200,1,1990-01-01\n",
        encoding="utf-8",
    )

    result = check_csv_file(csv_path, SimpleModel)

    assert result.ok is False
    assert result.num_errors == 1
    assert len(result.errors) == 1
    assert result.errors[0]["loc"] == (0, "age")


def test_check_csv_file_preserves_global_line_numbers_across_chunks(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "id,age,birthday\n1,20,1990-01-01\n2,21,1990-01-02\n-1,200,not-a-date\n",
        encoding="utf-8",
    )

    result = check_csv_file(csv_path, SimpleModel, chunk_size=2)

    assert result.ok is False
    assert result.num_errors == 3
    assert len(result.errors) == 3
    assert result.errors[0]["loc"] == (2, "id")
    assert result.errors[1]["loc"] == (2, "age")
    assert result.errors[2]["loc"] == (2, "birthday")


def test_check_csv_file_truncates_displayed_errors_but_counts_all_errors(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "id,age,birthday\n"
        "-1,200,not-a-date\n"
        "-2,201,still-not-a-date\n",
        encoding="utf-8",
    )

    result = check_csv_file(csv_path, SimpleModel, chunk_size=1, max_errors=1)

    assert result.ok is False
    assert result.num_errors == 6
    assert result.truncated is True
    assert len(result.errors) == 1
    assert result.errors[0]["loc"] == (0, "id")
