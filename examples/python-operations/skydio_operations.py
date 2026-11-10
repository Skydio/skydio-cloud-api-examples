"""
Operations API helpers shared by the scripts in this folder, built on SkydioAPIClient
(copied unchanged from the python-marker-crud example).

Endpoints used:
    GET /v0/operations                 (scope: Operations)
    GET /v0/operation/<id>             (scope: Operations)
    GET /v0/operation_reports          (scope: Operation Reports)
    GET /v0/operation_report/<id>      (scope: Operation Reports)
"""

import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterator, List, Optional

import requests
from dateutil.parser import isoparse

from skydio_api_client import SkydioAPIClient

MAX_PER_PAGE = 500

SCOPE_HINT = (
    "Check that the API token has the 'Operations' and 'Operation Reports' scopes "
    "(Integrations > API Tokens in Skydio Cloud) and that the Operations API is enabled "
    "for your organization (contact Skydio)."
)


class SkydioApiError(Exception):
    pass


def make_client() -> SkydioAPIClient:
    """Client for API_TOKEN, against SKYDIO_API_URL if set (e.g. an on-prem server)."""
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        raise SkydioApiError("API_TOKEN environment variable is not set.")
    api_url = os.getenv("SKYDIO_API_URL")
    return (
        SkydioAPIClient(api_token, url=api_url)
        if api_url
        else SkydioAPIClient(api_token)
    )


def api_get(
    client: SkydioAPIClient, endpoint: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """GET an endpoint and return its `data` payload, with a scope hint on auth failures."""
    params = {k: v for k, v in (params or {}).items() if v is not None}
    try:
        return client.get(endpoint, params=params).get("data", {})
    except requests.HTTPError as e:
        status = e.response.status_code
        try:
            message = e.response.json().get("error_message") or e.response.reason
        except ValueError:
            message = e.response.reason
        hint = {
            401: " Check that API_TOKEN is a valid API token for this server.",
            403: f" {SCOPE_HINT}",
        }.get(status, "")
        raise SkydioApiError(
            f"GET {endpoint} failed with {status}: {message}.{hint}"
        ) from e


def paginate(
    client: SkydioAPIClient,
    endpoint: str,
    key: str,
    params: Optional[Dict[str, Any]] = None,
    stop: Optional[Callable[[List[Dict[str, Any]]], bool]] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Yield every item under `key` across all pages of a list endpoint.

    `stop`, if given, is called with each page's items; returning True ends pagination early
    (useful for newest-first endpoints with a date cutoff).
    """
    page_number = 1
    while True:
        data = api_get(
            client,
            endpoint,
            {**(params or {}), "per_page": MAX_PER_PAGE, "page_number": page_number},
        )
        items = data.get(key, [])
        yield from items

        total_pages = data.get("pagination", {}).get("total_pages", 1)
        if not items or page_number >= total_pages or (stop and stop(items)):
            return
        page_number += 1


def to_api_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _parse_timestamp(value: str) -> datetime:
    parsed = isoparse(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_api_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse an API timestamp into an aware datetime (UTC if it has no offset)."""
    return _parse_timestamp(value) if value else None


def list_operations(
    client: SkydioAPIClient,
    state: Optional[str] = None,
    start_since: Optional[datetime] = None,
    start_before: Optional[datetime] = None,
    end_since: Optional[datetime] = None,
    end_before: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """List operations. `state` is one of INACTIVE, ACTIVE, CLOSED."""
    params = {
        "state": state,
        "start_since": to_api_datetime(start_since),
        "start_before": to_api_datetime(start_before),
        "end_since": to_api_datetime(end_since),
        "end_before": to_api_datetime(end_before),
    }
    return list(paginate(client, "/v0/operations", "operations", params))


def get_operation(client: SkydioAPIClient, operation_id: str) -> Dict[str, Any]:
    return api_get(client, f"/v0/operation/{operation_id}")["operation"]


def list_operation_reports(
    client: SkydioAPIClient,
    operation_id: Optional[str] = None,
    stop: Optional[Callable[[List[Dict[str, Any]]], bool]] = None,
) -> List[Dict[str, Any]]:
    """
    List submitted operation reports, newest first. Without `operation_id` this returns every
    submitted report in the organization.
    """
    return list(
        paginate(
            client,
            "/v0/operation_reports",
            "operation_reports",
            {"operation_id": operation_id},
            stop,
        )
    )


def get_operation_report(
    client: SkydioAPIClient, operation_report_id: str
) -> Dict[str, Any]:
    return api_get(client, f"/v0/operation_report/{operation_report_id}")[
        "operation_report"
    ]


def _events_of_type(operation: Dict[str, Any], event_type: str) -> List[Dict[str, Any]]:
    return [
        e
        for e in operation.get("events", [])
        if e.get("event_type") == event_type and e.get("event_time")
    ]


def first_event(operation: Dict[str, Any], event_type: str) -> Optional[Dict[str, Any]]:
    """Earliest event of `event_type` on an operation, or None."""
    matches = _events_of_type(operation, event_type)
    return (
        min(matches, key=lambda e: _parse_timestamp(e["event_time"]))
        if matches
        else None
    )


def last_event(operation: Dict[str, Any], event_type: str) -> Optional[Dict[str, Any]]:
    """Latest event of `event_type` on an operation, or None."""
    matches = _events_of_type(operation, event_type)
    return (
        max(matches, key=lambda e: _parse_timestamp(e["event_time"]))
        if matches
        else None
    )


def vehicle_serials(operation: Dict[str, Any]) -> List[str]:
    """Distinct vehicle serials from an operation's flights, in first-seen order."""
    serials = [f.get("vehicle_serial") for f in operation.get("flights", [])]
    return list(dict.fromkeys(s for s in serials if s))
