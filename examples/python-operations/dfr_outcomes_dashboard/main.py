"""
Export DFR outcomes for Skydio Cloud operations to CSV and a self-contained HTML dashboard.

    python dfr_outcomes_dashboard/main.py --since 2026-10-01

Each operation started since `--since` becomes one row, combining on-scene times from the
operation timeline with the DFR Outcomes answers from its submitted report.
"""

import argparse
import csv
import html
import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

import plotly.graph_objects as go
import plotly.io as pio

from skydio_operations import (
    SkydioApiError,
    first_event,
    list_operation_reports,
    list_operations,
    make_client,
    parse_api_datetime,
)

# Question titles in the Skydio-provided DFR Outcomes section of operation reports.
TYPE_OF_INCIDENT = "Type of incident"
FIRST_ON_SCENE = "Did the drone get to the scene first?"
CLEARED_WITHOUT_PATROL = "Did the drone clear the call without patrol resources?"
DRONE_ASSISTED = "How did the drone assist with the call?"


def event_time(operation, event_type):
    event = first_event(operation, event_type)
    return parse_api_datetime(event["event_time"]) if event else None


def seconds_between(start, end):
    return (end - start).total_seconds() if start and end else None


def as_list(answer):
    if answer is None:
        return []
    return answer if isinstance(answer, list) else [answer]


def build_row(operation, report):
    answers = {q["title"]: q["answer"] for q in (report or {}).get("response", [])}
    created = event_time(operation, "INCIDENT_CREATED")
    responded = event_time(operation, "INCIDENT_RESPONDED")
    arrived = event_time(operation, "VEHICLE_ARRIVED_ON_SCENE")
    arrival = first_event(operation, "VEHICLE_ARRIVED_ON_SCENE") or {}
    return {
        "operation_id": operation["operation_id"],
        "title": operation.get("title", ""),
        "started_at": event_time(operation, "OPERATION_CREATED"),
        "incident_ids": ", ".join(operation.get("incident_ids", [])),
        "time_to_respond_s": seconds_between(created, responded),
        "time_to_arrival_s": seconds_between(responded, arrived),
        "on_scene_source": arrival.get("on_scene_source"),
        "report_submitted": report is not None,
        "type_of_incident": ", ".join(as_list(answers.get(TYPE_OF_INCIDENT))),
        "first_on_scene": answers.get(FIRST_ON_SCENE),
        "cleared_without_patrol": answers.get(CLEARED_WITHOUT_PATROL),
        "drone_assisted": ", ".join(as_list(answers.get(DRONE_ASSISTED))),
    }


def fetch_rows(since):
    client = make_client()
    operations = list_operations(client, start_since=since)
    # Reports come newest first, so stop paging once a whole page is older than `since`.
    reports = list_operation_reports(
        client,
        stop=lambda page: all(
            parse_api_datetime(r["last_edited_at"]) < since for r in page
        ),
    )
    reports_by_operation = {r["operation_id"]: r for r in reports}
    print(f"Fetched {len(operations)} operations and {len(reports)} reports")
    rows = [
        build_row(op, reports_by_operation.get(op["operation_id"])) for op in operations
    ]
    return sorted(rows, key=lambda r: r["started_at"] or since, reverse=True)


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0]) if rows else ["operation_id"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved CSV to {path}")


# ----------------- HTML ------------------


def minutes(values):
    values = [v for v in values if v is not None]
    return f"{statistics.mean(values) / 60:.1f} min" if values else "-"


def bar_chart(title, values):
    """Horizontal bar chart of how often each comma-separated answer appears."""
    counts = Counter(v for value in values if value for v in value.split(", "))
    fig = go.Figure(
        go.Bar(x=list(counts.values()), y=list(counts.keys()), orientation="h")
    )
    fig.update_layout(
        title=title, height=320, template="plotly_white", margin={"l": 200}
    )
    return fig


def operations_per_day_chart(rows):
    days = Counter(r["started_at"].date() for r in rows if r["started_at"])
    fig = go.Figure(go.Bar(x=list(days.keys()), y=list(days.values())))
    fig.update_layout(title="Operations per day", height=320, template="plotly_white")
    return fig


def write_html(rows, since, path):
    tiles = {
        "Operations": len(rows),
        "Reports submitted": sum(r["report_submitted"] for r in rows),
        "First on scene": sum(r["first_on_scene"] == "Yes" for r in rows),
        "Cleared without patrol": sum(
            r["cleared_without_patrol"] == "Yes" for r in rows
        ),
        "Arrived on scene": sum(r["time_to_arrival_s"] is not None for r in rows),
        "Avg. time to respond": minutes(r["time_to_respond_s"] for r in rows),
        "Avg. time to arrival": minutes(r["time_to_arrival_s"] for r in rows),
    }
    tiles_html = "".join(
        f'<div class="tile"><div>{name}</div><b>{value}</b></div>'
        for name, value in tiles.items()
    )

    figures = [
        operations_per_day_chart(rows),
        bar_chart("Type of incident", [r["type_of_incident"] for r in rows]),
        bar_chart("How the drone assisted", [r["drone_assisted"] for r in rows]),
        bar_chart("Arrival on scene detected by", [r["on_scene_source"] for r in rows]),
    ]
    charts_html = "".join(
        f'<div class="card">{pio.to_html(fig, full_html=False, include_plotlyjs=(i == 0))}</div>'
        for i, fig in enumerate(figures)
    )

    columns = ["started_at", "title", "incident_ids", "type_of_incident",
               "first_on_scene", "cleared_without_patrol", "drone_assisted",
               "on_scene_source", "report_submitted"]  # fmt: skip
    table_html = "<tr>" + "".join(f"<th>{c}</th>" for c in columns) + "</tr>"
    for row in rows[:100]:
        cells = "".join(
            f"<td>{html.escape('' if row[c] is None else str(row[c]))}</td>"
            for c in columns
        )
        table_html += f"<tr>{cells}</tr>"

    page = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>DFR Outcomes</title>
<style>
  body {{ font-family: sans-serif; background: #f4f5f7; margin: 0; padding: 24px; }}
  .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .tiles {{ grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); margin-bottom: 16px; }}
  .tile, .card {{ background: white; border: 1px solid #e1e4e8; border-radius: 8px; padding: 16px; }}
  .tile b {{ display: block; font-size: 28px; margin-top: 8px; }}
  table {{ border-collapse: collapse; width: 100%; background: white; margin-top: 16px; font-size: 13px; }}
  th, td {{ border-bottom: 1px solid #e1e4e8; padding: 6px 8px; text-align: left; }}
</style>
</head>
<body>
<h1>DFR Outcomes</h1>
<p>Operations started since {since:%Y-%m-%d}. Generated {datetime.now():%Y-%m-%d %H:%M}.</p>
<div class="grid tiles">{tiles_html}</div>
<div class="grid">{charts_html}</div>
<table>{table_html}</table>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Saved dashboard to {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Skydio API - Export DFR outcomes to CSV and an HTML dashboard."
    )
    parser.add_argument(
        "--since",
        type=parse_api_datetime,
        default=datetime.now(timezone.utc) - timedelta(days=30),
        help="Include operations started at or after this ISO 8601 date/time (default: 30 days ago)",
    )
    parser.add_argument("--csv", default="dfr_outcomes.csv", help="CSV output path")
    parser.add_argument(
        "--html", default="dfr_outcomes.html", help="HTML dashboard output path"
    )
    args = parser.parse_args()

    try:
        rows = fetch_rows(args.since)
    except SkydioApiError as e:
        print(f"Error: {e}")
        return 1

    write_csv(rows, args.csv)
    write_html(rows, args.since, args.html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
