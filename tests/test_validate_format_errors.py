import pandas as pd
from datavalgen.reporterrors import format_val_errors
from datavalgen.validate import validate_dataframe
from .test_validate import SimpleModel


# We want to stay consistent with how we report errors, hence the hardcorded expected strings.
# For now, I'd rather fix tests than risk misreporting errors.
def test_validate_format_errors():
    df = pd.DataFrame(
        [
            {"id": -1, "age": 200, "birthday": "not-a-date"},
        ]
    )

    errors = validate_dataframe(df, SimpleModel)

    text = format_val_errors(errors, max_errors=10)

    errors_lines = text.splitlines()

    assert len(errors_lines) == 6

    assert errors_lines[0] == "❌ Line 2, column 'id': Input should be greater than 0."
    assert errors_lines[1] == "   Got: '-1'."
    assert errors_lines[2] == "❌ Line 2, column 'age': Input should be less than or equal to 120."
    assert errors_lines[3] == "   Got: '200'."
    assert errors_lines[4] == "❌ Line 2, column 'birthday': Input should be a valid date or datetime, invalid character in year."
    assert errors_lines[5] == "   Got: 'not-a-date'."

