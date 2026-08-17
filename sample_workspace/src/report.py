from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


def summarize_sales(csv_path: Path) -> dict:
    totals = defaultdict(float)
    units = 0
    rows = 0
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            units += int(row["units"])
            totals[row["region"]] += float(row["revenue"])
    return {
        "rows": rows,
        "units": units,
        "revenue_by_region": dict(totals),
        "total_revenue": sum(totals.values()),
    }
