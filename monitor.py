"""Validate a CSV dataset against a JSON data-quality contract."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path


def check_value(value: str, expected_type: str) -> bool:
    try:
        if expected_type == "integer":
            int(value)
        elif expected_type == "number":
            float(value)
        elif expected_type == "date":
            date.fromisoformat(value)
        elif expected_type != "string":
            raise ValueError(f"Unsupported contract type: {expected_type}")
        return True
    except ValueError:
        return False


def validate(rows: list[dict[str, str]], fieldnames: list[str], contract: dict, as_of: date) -> list[dict]:
    failures: list[dict] = []
    columns = contract["columns"]
    missing_columns = sorted(set(columns) - set(fieldnames))
    if missing_columns:
        failures.append({"rule": "required_columns", "columns": missing_columns})
        return failures

    unique_sets: dict[str, set[str]] = {name: set() for name, spec in columns.items() if spec.get("unique")}
    for row_number, row in enumerate(rows, start=2):
        for name, spec in columns.items():
            value = (row.get(name) or "").strip()
            if not value:
                if spec.get("required", False):
                    failures.append({"rule": "not_null", "column": name, "row": row_number})
                continue
            if not check_value(value, spec.get("type", "string")):
                failures.append({"rule": "type", "column": name, "row": row_number, "expected": spec["type"]})
                continue
            if "accepted_values" in spec and value not in spec["accepted_values"]:
                failures.append({"rule": "accepted_values", "column": name, "row": row_number})
            if "minimum" in spec and float(value) < float(spec["minimum"]):
                failures.append({"rule": "minimum", "column": name, "row": row_number})
            if name in unique_sets:
                if value in unique_sets[name]:
                    failures.append({"rule": "unique", "column": name, "row": row_number})
                unique_sets[name].add(value)

    freshness = contract.get("freshness")
    if freshness:
        column = freshness["column"]
        dates = []
        for row in rows:
            try:
                dates.append(date.fromisoformat((row.get(column) or "").strip()))
            except ValueError:
                pass
        if not dates or (as_of - max(dates)).days > freshness["max_age_days"]:
            failures.append({"rule": "freshness", "column": column, "max_age_days": freshness["max_age_days"]})
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(),
                        help="Evaluation date (YYYY-MM-DD); defaults to today")
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    with args.data.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    failures = validate(rows, fieldnames, contract, args.as_of)
    report = {
        "dataset": str(args.data),
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": args.as_of.isoformat(),
        "row_count": len(rows),
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['status'].upper()}: {len(rows)} rows, {len(failures)} failure(s) -> {args.report}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
