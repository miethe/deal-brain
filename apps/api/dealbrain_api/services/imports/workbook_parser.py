"""Workbook parsing utilities for Excel and CSV files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas import DataFrame


class WorkbookParser:
    """Handles parsing of Excel and CSV files into normalized DataFrames."""

    @staticmethod
    def load_workbook(path: Path) -> dict[str, DataFrame]:
        """
        Load an Excel or CSV file into a dictionary of DataFrames.

        Args:
            path: Path to the workbook file (.xlsx, .xlsm, .xls, .csv, .tsv)

        Returns:
            Dictionary mapping sheet names to DataFrames with string columns

        Raises:
            ValueError: If file type is not supported
        """
        suffix = path.suffix.lower()
        if suffix in {".xlsx", ".xlsm", ".xls"}:
            sheets = pd.read_excel(path, sheet_name=None, dtype=object)
        elif suffix in {".csv", ".tsv"}:
            sep = "," if suffix == ".csv" else "\t"
            sheets = {path.stem: pd.read_csv(path, sep=sep, dtype=object)}
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        # Normalize all sheet names and column names to strings
        normalized: dict[str, DataFrame] = {}
        for name, df in sheets.items():
            dataframe = df if isinstance(df, DataFrame) else pd.DataFrame(df)
            dataframe.columns = [str(column) for column in dataframe.columns]
            normalized[name] = dataframe

        return normalized


__all__ = ["WorkbookParser"]
