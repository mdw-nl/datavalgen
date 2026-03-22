"""
Reads a CSV file and load it into a Pandas DataFrame.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

__all__ = [
    "read_csv_raw",
]


def read_csv_raw(csv_path: str | Path) -> pd.DataFrame:
    """
    Reads CSV using strings as dtype for every column and not interpreting any NAs.

    :param csv_path: Path to the CSV file.
    :return: DataFrame containing the data from the CSV file.
    """
    return pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_filter=False)
