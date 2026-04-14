from datavalgen.report_errors import format_val_errors
from datavalgen.validate import check_csv_file
from .test_validate import SimpleModel


def test_validate_format_errors(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "id,age,birthday\n-1,200,not-a-date\n",
        encoding="utf-8",
    )

    errors = list(check_csv_file(csv_path, SimpleModel).errors)
    text = format_val_errors(errors, max_errors=10)
    errors_lines = text.splitlines()

    assert len(errors_lines) == 6
    assert errors_lines[0] == "❌ Line 2, column 'id': Input should be greater than 0."
    assert errors_lines[1] == "   Got: '-1'."
    assert errors_lines[2] == "❌ Line 2, column 'age': Input should be less than or equal to 120."
    assert errors_lines[3] == "   Got: '200'."
    assert errors_lines[4] == "❌ Line 2, column 'birthday': Input should be a valid date or datetime, invalid character in year."
    assert errors_lines[5] == "   Got: 'not-a-date'."


def test_validate_format_errors_with_pre_truncated_input(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "id,age,birthday\n-1,200,not-a-date\n",
        encoding="utf-8",
    )

    errors = list(check_csv_file(csv_path, SimpleModel).errors[:1])
    text = format_val_errors(errors, max_errors=1, truncated=True)
    errors_lines = text.splitlines()

    assert errors_lines[0] == "❌ Line 2, column 'id': Input should be greater than 0."
    assert errors_lines[1] == "   Got: '-1'."
    assert errors_lines[2] == "... output truncated after the first 1 problem cells."


def test_validate_format_errors_with_zero_display_budget():
    text = format_val_errors([], max_errors=0, truncated=True)
    assert (
        text
        == "Validation found errors, but output was truncated because --max-errors is set to 0."
    )
