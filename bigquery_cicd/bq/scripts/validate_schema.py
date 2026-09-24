"""
validate_schema.py
Performs local structural checks on BigQuery DDL files.
The bq --dry_run is executed as a dedicated step in the GitHub Actions workflow.
"""

import sys
from pathlib import Path

SQL_FILE = Path(__file__).parent.parent / "schemas" / "sample_customers.sql"

REQUIRED_KEYWORDS = [
    "CREATE TABLE",
    "sample_customers",
    "PARTITION BY signup_date",
    "CLUSTER BY customer_id",
]


def main():
    # 1. File existence check
    if not SQL_FILE.exists():
        print(f"[ERROR] SQL file not found: {SQL_FILE}")
        sys.exit(1)

    sql = SQL_FILE.read_text(encoding="utf-8").strip()

    # 2. Empty file check
    if not sql:
        print("[ERROR] SQL file is empty.")
        sys.exit(1)

    # 3. Required keyword checks
    failed = False
    for keyword in REQUIRED_KEYWORDS:
        if keyword.lower() not in sql.lower():
            print(f"[ERROR] Validation failed — missing required keyword: '{keyword}'")
            failed = True

    if failed:
        sys.exit(1)

    print("[OK] All local SQL structure checks passed.")
    print(f"     File: {SQL_FILE}")
    print(f"     Size: {len(sql)} characters")


if __name__ == "__main__":
    main()