from pathlib import Path

from report import summarize_sales
from utils import workspace_root


def main() -> None:
    summary = summarize_sales(workspace_root() / "data" / "sales.csv")
    print(f"rows={summary['rows']}")
    print(f"units={summary['units']}")
    print(f"total_revenue={summary['total_revenue']}")


if __name__ == "__main__":
    main()
