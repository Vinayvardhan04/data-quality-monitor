# Data Quality Monitor

A small, runnable data observability project for CSV datasets. It checks schema, nulls, types, uniqueness, accepted values, and freshness using a declarative JSON contract. It writes a machine-readable report and exits nonzero when quality gates fail, so it can be called from an orchestration job or CI pipeline. The local implementation uses only Python's standard library.

## Why this project

Data pipelines are useful only when downstream users can trust their output. This project makes quality rules explicit and produces evidence for each run. It is a portfolio example, not a production monitoring service or a claim of deployed infrastructure.

## Quick start

```bash
python3 monitor.py --data sample_data/orders_clean.csv --contract contract.json --report report.json --as-of 2026-10-28
python3 monitor.py --data sample_data/orders_bad.csv --contract contract.json --report report.json --as-of 2026-10-28
```

The clean file should pass. The bad file intentionally contains a duplicate ID, an invalid amount, an unapproved status, and a missing date; the command exits with code `1` and records failures in `report.json`. The explicit `--as-of` makes this historical sample reproducible. Omit it for current production-like freshness checks.

## Contract

[`contract.json`](contract.json) defines the expected columns and rules. `order_id` is the unique key, `amount` must be a nonnegative number, `status` must be an approved value, and `order_date` must be an ISO date. Freshness is evaluated against the latest date **in the input file** with a configurable maximum age relative to the run date; sample dates are kept current for this demonstration.

## Output

The JSON report includes input path, row count, checked-at timestamp, a pass/fail summary, and each failed rule with affected row numbers. Do not include customer personal information in sample or report files. The sample data is fictional.

## Production extension

For production use, add a warehouse connector, durable history for trend analysis, dataset ownership and alert routing, secrets management, and bounded sampling for large datasets. See [design notes](docs/design.md).

## License

MIT.
