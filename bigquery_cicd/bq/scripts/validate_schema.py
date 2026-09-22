import subprocess
import sys
from pathlib import Path


SQL_FILE = Path(__file__).parent.parent / "schemas" / "sample_customers.sql"


def main():
    if not SQL_FILE.exists():
        print(f"SQL file not found: {SQL_FILE}")
        sys.exit(1)

    sql = SQL_FILE.read_text(encoding="utf-8").strip()

    if not sql:
        print("SQL file is empty.")
        sys.exit(1)

    required_text = [
        "CREATE TABLE",
        "sample_customers",
        "PARTITION BY signup_date",
        "CLUSTER BY customer_id",
    ]

    for item in required_text:
        if item.lower() not in sql.lower():
            print(f"Validation failed: missing '{item}'")
            sys.exit(1)

    print("SQL structure validation passed.")

    try:
        result = subprocess.run(
            [
                "bq",
                "query",
                "--use_legacy_sql=false",
                "--dry_run",
                sql,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("BigQuery dry-run failed:")
            print(result.stderr)
            sys.exit(1)

        print("BigQuery dry-run validation passed.")

    except FileNotFoundError:
        print("bq command was not found.")
        print("Install the Google Cloud CLI to run the local validation.")
        sys.exit(1)


if __name__ == "__main__":
    main()