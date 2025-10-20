"""Command line utility for downloading DART financial statements."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from core import DartExtractor


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_argument_group("Corporation lookup")
    group.add_argument("--corp-name", help="Exact company name registered at DART")
    group.add_argument("--corp-code", help="Unique 8-digit DART corporation code")
    group.add_argument("--stock-code", help="6-digit stock code (종목코드)")

    parser.add_argument("--api-key", help="Override the DART Open API key")
    parser.add_argument(
        "--no-demo-key",
        action="store_true",
        help="Disable the bundled public demo key and require an explicit API key.",
    )
    parser.add_argument(
        "--begin-date",
        default="20190101",
        help="Start date (YYYYMMDD) for the filings to include. Default: 20190101",
    )
    parser.add_argument(
        "--report-type",
        choices=["annual", "half", "quarter"],
        default="annual",
        help="Type of report to download from DART. Default: annual",
    )
    parser.add_argument(
        "--separate",
        action="store_true",
        help="Fetch separate financial statements instead of consolidated ones.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="When provided, save the statements into an Excel workbook at this path.",
    )
    parser.add_argument(
        "--statements",
        nargs="+",
        default=["bs", "cis", "is", "cf"],
        help="Specific statement keys to extract (default: bs cis is cf).",
    )

    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    corp_name = args.corp_name
    corp_code = args.corp_code
    stock_code = args.stock_code

    if not (corp_name or corp_code or stock_code):
        try:
            corp_name = input("조회할 회사명을 입력하세요: ").strip()
        except EOFError:
            pass

    if not (corp_name or corp_code or stock_code):
        print("회사 식별 정보를 하나 이상 입력해야 합니다.", file=sys.stderr)
        return 2

    extractor = DartExtractor(api_key=args.api_key, allow_demo_key=not args.no_demo_key)

    try:
        result = extractor.extract(
            corp_name=corp_name if corp_name else None,
            corp_code=corp_code if corp_code else None,
            stock_code=stock_code if stock_code else None,
            begin_date=args.begin_date,
            report_type=args.report_type,
            separate=args.separate,
            statement_keys=args.statements,
        )
    except Exception as exc:  # pragma: no cover - CLI feedback path
        print(f"데이터를 가져오는 중 오류가 발생했습니다: {exc}", file=sys.stderr)
        return 1

    if args.output:
        path = result.to_excel(args.output)
        print(f"재무제표를 '{path}' 파일로 저장했습니다.")
    else:
        _print_summary(result.statements)

    return 0


def _print_summary(statements: dict[str, pd.DataFrame]) -> None:
    if not statements:
        print("가져온 재무제표가 없습니다.")
        return

    for key, frame in statements.items():
        if frame is None or frame.empty:
            print(f"[{key}] 빈 데이터")
            continue
        preview = frame.head(5)
        print(f"[{key}] 상위 5개 행:")
        with pd.option_context("display.max_rows", None, "display.max_columns", None):
            print(preview)
        print("-")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
