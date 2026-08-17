from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from report import summarize_sales


def test_summarize_sales():
    path = Path(__file__).resolve().parents[1] / "data" / "sales.csv"
    summary = summarize_sales(path)
    assert summary["rows"] == 10
    assert summary["units"] == 95
    assert summary["total_revenue"] == 2070.0
