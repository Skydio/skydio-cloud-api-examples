"""
List Skydio Cloud operations, optionally filtered by state and start/end time, and
optionally save them to CSV.

    python list_operations.py --state CLOSED --start-since 2026-10-01 --csv operations.csv
"""

import argparse
import csv
import sys

from skydio_operations import (
    SkydioApiError,
    last_event,
    list_operations,
    make_client,
    parse_api_datetime,
    vehicle_serials,
)

CSV_FIELDNAMES = [
    "operation_id",
    "title",
    "state",
    "incident_ids",
    "vehicle_serials",
    "closed_at",
]


def build_row(operation):
    closed = last_event(operation, "OPERATION_CLOSED")
    return {
        "operation_id": operation["operation_id"],
        "title": operation.get("title", ""),
        "state": operation.get("state", ""),
        "incident_ids": "; ".join(operation.get("incident_ids", [])),
        "vehicle_serials": "; ".join(vehicle_serials(operation)),
        "closed_at": closed["event_time"] if closed else "",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Skydio API - List operations example."
    )
    parser.add_argument("--state", choices=["INACTIVE", "ACTIVE", "CLOSED"])
    parser.add_argument(
        "--start-since", type=parse_api_datetime, help="ISO 8601 date or time"
    )
    parser.add_argument(
        "--start-before", type=parse_api_datetime, help="ISO 8601 date or time"
    )
    parser.add_argument(
        "--end-since", type=parse_api_datetime, help="ISO 8601 date or time"
    )
    parser.add_argument(
        "--end-before", type=parse_api_datetime, help="ISO 8601 date or time"
    )
    parser.add_argument("--csv", help="Path to CSV file where results will be saved")
    args = parser.parse_args()

    try:
        operations = list_operations(
            make_client(),
            state=args.state,
            start_since=args.start_since,
            start_before=args.start_before,
            end_since=args.end_since,
            end_before=args.end_before,
        )
    except SkydioApiError as e:
        print(f"Error: {e}")
        return 1

    rows = [build_row(op) for op in operations]
    print(f"{'Operation ID':<38} {'State':<9} {'Closed at':<33} Title")
    print("-" * 100)
    for row in rows:
        print(
            f"{row['operation_id']:<38} {row['state']:<9} {row['closed_at']:<33} {row['title']}"
        )
    print(f"\n{len(rows)} operations")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved to {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
