# Design notes

The monitor reads a finite CSV file into memory and evaluates a contract in one pass. It reports row numbers using the source CSV's header as line 1. Rules are deterministic except freshness, which uses the system date. The tool intentionally does not record failing cell values in the report, reducing accidental exposure of sensitive data.

This design is suitable for small batch files. For larger datasets, stream rows, aggregate failures, and cap examples in the report. For warehouses, push row-level checks into SQL and record the contract version and run ID. Add alerting only after defining dataset ownership and acceptable freshness windows.
