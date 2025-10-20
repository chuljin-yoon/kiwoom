"""Utilities for extracting financial statements from DART."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

try:  # pragma: no cover - import guard for helpful error message
    import dart_fss as dart
except ImportError as exc:  # pragma: no cover - executed only when dependency missing
    raise ImportError(
        "dart_fss is required to run the extractor. Install the project dependencies "
        "with 'pip install -r requirements.txt' or via Poetry."
    ) from exc

# A publicly documented demo key that ships with the dart-fss project. The user can
# override it by setting the DART_API_KEY environment variable.
DEFAULT_DEMO_API_KEY = "66ce66618f4850247aa36d3d0bea34737980af17"


@dataclass
class ExtractResult:
    """Container for the extracted financial statement tables."""

    corp_name: str
    corp_code: str
    statements: Dict[str, pd.DataFrame]

    def to_excel(self, destination: Path | str) -> Path:
        """Persist the extracted statements to an Excel workbook."""

        path = Path(destination)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for sheet_name, frame in self.statements.items():
                if frame is None or frame.empty:
                    continue
                safe_name = sheet_name[:31] or "Sheet"
                frame.to_excel(writer, sheet_name=safe_name)
        return path


class DartExtractor:
    """High level helper around :mod:`dart_fss` for bank analysis workflows."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        allow_demo_key: bool = True,
    ) -> None:
        key = (api_key or os.getenv("DART_API_KEY", "")).strip()
        if not key and allow_demo_key:
            key = DEFAULT_DEMO_API_KEY

        self.api_key = key
        if self.api_key:
            dart.set_api_key(api_key=self.api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(  # noqa: D401 - short description inherited from class docstring
        self,
        *,
        corp_name: Optional[str] = None,
        corp_code: Optional[str] = None,
        stock_code: Optional[str] = None,
        begin_date: str = "20190101",
        report_type: str = "annual",
        separate: bool = False,
        statement_keys: Iterable[str] = ("bs", "cis", "is", "cf"),
    ) -> ExtractResult:
        """Fetch financial statements for the requested corporation."""

        corp = self._resolve_corp(corp_name=corp_name, corp_code=corp_code, stock_code=stock_code)
        statements = self._collect_statements(
            corp,
            begin_date=begin_date,
            report_type=report_type,
            separate=separate,
            keys=tuple(statement_keys),
        )
        return ExtractResult(corp_name=corp.corp_name, corp_code=corp.corp_code, statements=statements)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _collect_statements(
        corp: "dart.corp.Corp",
        *,
        begin_date: str,
        report_type: str,
        separate: bool,
        keys: Iterable[str],
    ) -> Dict[str, pd.DataFrame]:
        fs = corp.extract_fs(
            bgn_de=begin_date,
            report_tp=report_type,
            separate=separate,
            progressbar=False,
        )

        collected: Dict[str, pd.DataFrame] = {}
        for key in keys:
            statement = None
            try:
                statement = fs[key]
            except (KeyError, TypeError):
                statement = getattr(fs, key, None)
            if statement is None:
                continue

            frame = _statement_to_dataframe(statement)
            if frame is not None:
                collected[key] = frame
        return collected

    @staticmethod
    def _resolve_corp(
        *,
        corp_name: Optional[str],
        corp_code: Optional[str],
        stock_code: Optional[str],
    ) -> "dart.corp.Corp":
        corp_list = dart.get_corp_list()

        if corp_code:
            corp = corp_list.find_by_corp_code(corp_code)
            if corp:
                return corp

        if stock_code:
            corp = corp_list.find_by_stock_code(stock_code)
            if corp:
                return corp

        if corp_name:
            matches = corp_list.find_by_corp_name(corp_name, exactly=True)
            if matches:
                return matches[0]

        raise ValueError(
            "Corporation could not be resolved. Provide either 'corp_name', "
            "'corp_code' or 'stock_code'."
        )


def _statement_to_dataframe(statement: object) -> Optional[pd.DataFrame]:
    """Attempt to coerce the given statement into a :class:`~pandas.DataFrame`."""

    if isinstance(statement, pd.DataFrame):
        return statement

    to_dataframe = getattr(statement, "to_dataframe", None)
    if callable(to_dataframe):
        try:
            frame = to_dataframe()
        except Exception:  # pragma: no cover - defensive against upstream quirks
            frame = None
        if isinstance(frame, pd.DataFrame):
            return frame

    flatten = getattr(statement, "flatten", None)
    if callable(flatten):
        try:
            frame = flatten()
        except Exception:  # pragma: no cover - defensive against upstream quirks
            frame = None
        if isinstance(frame, pd.DataFrame):
            return frame

    return None


__all__ = ["DartExtractor", "ExtractResult"]
