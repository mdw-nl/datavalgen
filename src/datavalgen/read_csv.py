"""CSV read helpers used by validation paths."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

__all__ = [
    "CSV_READ_KWARGS",
    "read_csv_columns",
    "iter_csv_chunks",
]

CSV_READ_KWARGS = {
    "dtype": str,
    "keep_default_na": False,
    "na_filter": False,
}

def read_csv_columns(csv_path: str | Path) -> tuple[str, ...]:
    """
    Read only the CSV header and return the column names in file order.

    :param csv_path: Path to the CSV file.
    :return: Column names from the CSV header.
    """
    df = pd.read_csv(csv_path, nrows=0, **CSV_READ_KWARGS)
    return tuple(str(column) for column in df.columns)


def iter_csv_chunks(
    csv_path: str | Path,
    *,
    usecols: Sequence[str] | None = None,
    chunksize: int = 5000,
) -> Iterable[pd.DataFrame]:
    """
    Iterate over the CSV in chunks while preserving raw-string parsing semantics.

    :param csv_path: Path to the CSV file.
    :param usecols: Optional subset of columns to read.
    :param chunksize: Number of rows per chunk.
    :return: Iterable of DataFrames, one per chunk.
    """
    return pd.read_csv(
        csv_path,
        usecols=list(usecols) if usecols is not None else None,
        chunksize=chunksize,
        **CSV_READ_KWARGS,
    )
