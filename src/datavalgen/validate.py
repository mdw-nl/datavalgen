from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence, cast

from pydantic import BaseModel, TypeAdapter
from pydantic_core import ErrorDetails, ValidationError

from datavalgen.check_result import CheckResult
from datavalgen.read_csv import iter_csv_chunks, read_csv_columns


@dataclass(frozen=True)
class CsvCheckResult:
    """
    Result shape for CSV validation that keeps exact error counts separate from
    the sampled errors retained for reporting.
    """

    errors: tuple[ErrorDetails, ...] = ()
    warnings: tuple[str, ...] = ()
    num_errors: int = 0
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.num_errors == 0


def _model_columns(model: type[BaseModel]) -> list[str]:
    return list(model.model_fields.keys())


def check_column_names(
    columns: Sequence[str], model: type[BaseModel]
) -> CheckResult[str]:
    """
    Compare a sequence of CSV column names to the model's field names.
    """
    expected = set(_model_columns(model))
    actual = set(columns)

    missing = expected - actual
    extra = actual - expected

    error_lines: list[str] = []
    warning_lines: list[str] = []

    if missing:
        error_lines.append(f"Missing expected columns: {missing}")
    if extra:
        warning_lines.append(f"Unexpected columns: {extra}")

    return CheckResult(
        errors=tuple(error_lines),
        warnings=tuple(warning_lines),
    )

def _prefix_row_index(error: ErrorDetails, row_index: int) -> ErrorDetails:
    """
    Put the zero-based CSV row index at the front of the error `loc` tuple.

    Pydantic returns field errors relative to the validated row dict, so
    `error["loc"]` might be `("age",)`. We rewrite that `loc` value to include
    the CSV row index so downstream error formatting can report the correct line
    in the original file.

    Example:
        `error["loc"] == ("age",)` for the CSV row with zero-based index `7`
        becomes `error["loc"] == (7, "age")`.
    """
    prefixed = dict(error)
    prefixed["loc"] = (row_index, *tuple(error["loc"]))
    return cast(ErrorDetails, prefixed)


def _iter_row_dicts(
    chunk, columns: Sequence[str]
) -> Iterable[dict[str, object]]:
    for row in chunk.itertuples(index=False, name=None):
        yield dict(zip(columns, row))


def check_csv_file(
    csv_path: str | Path,
    model: type[BaseModel],
    *,
    chunk_size: int = 5000,
    max_errors: int | None = 10,
) -> CsvCheckResult:
    """
    Validate a CSV file chunk-by-chunk to keep memory bounded.

    We keep the current parsing semantics by still using pandas with
    `dtype=str`, `keep_default_na=False`, and `na_filter=False`, but we no
    longer materialize the whole file or convert it to one giant list of dicts.
    """
    columns = read_csv_columns(csv_path)
    column_check = check_column_names(columns, model)
    # We fail fast on header mismatches before starting the chunk loop. Row-wise
    # validation only makes sense once we know the expected model columns exist.
    if column_check.errors:
        return CsvCheckResult(
            warnings=column_check.warnings,
            num_errors=len(column_check.errors),
        )

    model_columns = _model_columns(model)
    # We build one reusable Pydantic validator for the selected model and apply
    # it to each row dict in turn, instead of validating the whole CSV as one
    # big list.
    adapter = TypeAdapter(model)

    # We keep exact counts for the whole file, but we only retain a bounded
    # sample of problem cells for human-readable output.
    # Sample of errors we keep in memory for later formatting/output.
    stored_errors: list[ErrorDetails] = []
    # Distinct problem cells we have decided to show, e.g. `(7, "age")`.
    # This is for max_errors
    shown_problem_keys: set[tuple[object, ...]] = set()
    num_errors = 0
    truncated = False
    # Each chunk starts its own row index at zero, so we carry a running offset
    # to keep error locations aligned with the original CSV line numbers.
    row_offset = 0

    # iterate thru chunks
    for chunk in iter_csv_chunks(
        csv_path, usecols=model_columns, chunksize=chunk_size
    ):
        # iterate thru rows in a chunck
        for chunk_index, row_dict in enumerate(_iter_row_dicts(chunk, model_columns)):
            global_row_index = row_offset + chunk_index
            try:
                adapter.validate_python(row_dict)
            except ValidationError as exc:
                row_errors = cast(
                    tuple[ErrorDetails, ...], tuple(exc.errors(include_url=False))
                )
                num_errors += len(row_errors)

                for error in row_errors:
                    # Example flow for a bad `age` cell on CSV row 7:
                    #   error["loc"] == ("age",)
                    #   prefixed["loc"] == (7, "age")
                    #   key == (7, "age")
                    prefixed = _prefix_row_index(error, global_row_index)
                    # `prefixed["loc"]` should already be a tuple here.
                    key = prefixed["loc"]
                    # `max_errors=None` means we keep every problem cell, which is
                    # mostly useful for tests or small files.
                    if max_errors is None:
                        shown_problem_keys.add(key)
                        stored_errors.append(prefixed)
                        continue

                    # If we already decided to display this cell, we keep any
                    # extra errors for the same cell so multi-rule failures stay
                    # grouped together in the formatter.
                    if key in shown_problem_keys:
                        stored_errors.append(prefixed)
                        continue

                    if len(shown_problem_keys) < max_errors:
                        shown_problem_keys.add(key)
                        stored_errors.append(prefixed)
                    else:
                        # We still keep counting after we stop storing display
                        # samples so `safe_validate` can return the true total.
                        truncated = True

        row_offset += len(chunk)

    return CsvCheckResult(
        errors=tuple(stored_errors),
        warnings=column_check.warnings,
        num_errors=num_errors,
        truncated=truncated,
    )
