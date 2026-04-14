from collections import defaultdict

from pydantic_core import ErrorDetails


def format_val_errors(
    errors: list[ErrorDetails],
    max_errors: int = 10,
    *,
    truncated: bool = False,
) -> str:
    """
    Format Pydantic v2 validation errors into a compact, human-readable string
    (with new lines).

    The function expects a list of `ErrorDetails` (the dicts you get from
    `ValidationError.errors()` in Pydantic v2). It groups "cell-level" errors
    by (row_index, field_name) when the error location begins with an integer
    (e.g., `(3, "age", ...)` meaning row 3, field "age"). Other errors are
    treated as "model-level" (e.g., `__root__` or custom validators not tied
    to a specific field).

    Row numbers are displayed as `row_index + 2` to account for zero-based
    indexing and a single header row. So DataFrame row 0 → “Line 2”. Line 1 is
    the header with column names. Just makes this easier for folks using simple
    editors to quickly edit/view their CSVs.

    Args:
        errors: A list of Pydantic `ErrorDetails` dictionaries.
        max_errors: Maximum number of distinct problem *cells* (row, column
            pairs) to print before truncating with a summary line.
        truncated: Whether the caller already truncated the input error list and
            therefore only wants a generic truncation note.

    Returns:
        str: A human-readable multi-line summary. If `errors` is empty, returns
            "✅ No validatoin errors found."
    """
    if not errors:
        if truncated:
            return (
                f"Validation found errors, but output was truncated because "
                f"--max-errors is set to {max_errors}."
            )
        return "✅ No validation errors found."

    cell_errs: dict[tuple[int, str], list[ErrorDetails]] = defaultdict(list)
    model_errs: list[ErrorDetails] = []

    for err in errors:
        loc = err["loc"]
        # Cell-level errors look like (row_idx, "field_name", ...).
        # We narrow both tuple elements so static type checkers know key type.
        if len(loc) >= 2 and isinstance(loc[0], int) and isinstance(loc[1], str):
            row = loc[0]
            col = loc[1]
            cell_errs[(row, col)].append(err)
        else:
            # Model-level errors are not specific to a cell
            # they can come from custom validators
            model_errs.append(err)

    lines: list[str] = []

    # Pretty-print cell-level problems
    displayed_cell_errs = list(cell_errs.items())[:max_errors]
    for (row, col), errs in displayed_cell_errs:
        joined = "\n   Or: ".join(e["msg"] for e in errs)
        lines.append(f"❌ Line {row + 2}, column '{col}': {joined}.")
        lines.append(f"   Got: '{errs[0]['input']}'.")
    if len(cell_errs) > max_errors:
        lines.append(f"... and {len(cell_errs) - max_errors} more problem cells.")
        lines.append(
            "   (Use --max-errors N to increase the number of reported cells to N.)"
        )
    elif truncated:
        lines.append(f"... output truncated after the first {max_errors} problem cells.")
        lines.append(
            "   (Use --max-errors N to increase the number of reported cells to N.)"
        )

    # Print any model-level
    for err in model_errs:
        loc_str = ".".join(str(x) for x in err["loc"]) or "__root__"
        if loc_str.isdigit():
            loc_str = int(loc_str) + 2
        lines.append(f"❌ Line {loc_str}: {err['msg']}")

    return "\n".join(lines)
