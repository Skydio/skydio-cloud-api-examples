"""
Print one Skydio Cloud operation: its details, event timeline, and the questions and
answers from each submitted operation report.

    python get_operation.py <operation_id>
"""

import argparse
import sys

from skydio_operations import (
    SkydioApiError,
    get_operation,
    list_operation_reports,
    make_client,
    vehicle_serials,
)


def describe_event(event):
    parts = []
    if event.get("user"):
        parts.append(event["user"].get("email", ""))
    if event.get("vehicle"):
        parts.append(event["vehicle"].get("vehicle_serial", ""))
    if event.get("marker"):
        parts.append(f"incident {event['marker'].get('incident_id', '')}".strip())
    if event.get("on_scene_source"):
        parts.append(f"on scene via {event['on_scene_source']}")
    if event.get("operation_report"):
        parts.append(f"report v{event['operation_report']['report_version']}")
    return ", ".join(p for p in parts if p)


def format_answer(question):
    answer = question.get("answer")
    if answer is None:
        text = "(no answer)"
    elif isinstance(answer, list):
        text = ", ".join(answer)
    else:
        text = answer
    if question.get("comment"):
        text += f"  [comment: {question['comment']}]"
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Skydio API - Get an operation with its timeline and reports."
    )
    parser.add_argument("operation_id")
    args = parser.parse_args()

    try:
        client = make_client()
        operation = get_operation(client, args.operation_id)
        reports = list_operation_reports(client, operation_id=args.operation_id)
    except SkydioApiError as e:
        print(f"Error: {e}")
        return 1

    print(f"Operation:  {operation.get('title', '')} ({operation['operation_id']})")
    print(f"State:      {operation.get('state', '')}")
    print(f"Incidents:  {', '.join(operation.get('incident_ids', [])) or '-'}")
    print(f"Vehicles:   {', '.join(vehicle_serials(operation)) or '-'}")
    print(
        f"Users:      {', '.join(u.get('email', '') for u in operation.get('users', [])) or '-'}"
    )

    print("\nTimeline")
    for event in operation.get("events", []):
        print(
            f"  {event['event_time']}  {event['event_type']:<28} {describe_event(event)}"
        )

    if not reports:
        print("\nNo submitted operation reports.")
    for report in reports:
        editor = report.get("last_edited_by", {}).get("email") or "unknown"
        print(
            f"\nReport {report['operation_report_id']} "
            f"(v{report.get('report_version', '?')}, {report['last_edited_at']}, {editor})"
        )
        for question in report.get("response", []):
            print(f"  {question['title']}")
            print(f"    {format_answer(question)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
