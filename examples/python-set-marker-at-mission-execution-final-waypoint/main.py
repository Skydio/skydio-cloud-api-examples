#!/usr/bin/env python3

import os
import sys
import argparse
import arrow
import requests

SKYDIO_API_BASE_URL = "https://api.skydio.com/api/v0"


def get_headers(auth_token):
    return {"Authorization": auth_token, "Accept": "application/json"}


def get_mission_runs_for_flight(flight_id, auth_token):
    url = f"{SKYDIO_API_BASE_URL}/mission_runs"
    params = {"flight_id": flight_id, "per_page": 25, "page_number": 1}

    response = requests.get(url, headers=get_headers(auth_token), params=params)
    response.raise_for_status()
    return response.json()


def get_mission_template_by_id(template_uuid, auth_token):
    url = f"{SKYDIO_API_BASE_URL}/mission/template/{template_uuid}"
    response = requests.get(url, headers=get_headers(auth_token))
    response.raise_for_status()
    return response.json()


def upsert_marker(
    auth_token,
    latitude,
    longitude,
    description,
    event_time,
    marker_type="INCIDENT",
    source_name="integration_test",
    title="Mission Waypoint",
):
    """
    Step 4) Create or update a marker at the given latitude/longitude.

    NOTE: 'type' must be at the top level for this endpoint.
    """
    url = f"{SKYDIO_API_BASE_URL}/marker"

    payload = {
        "type": marker_type,  # Must be top-level for the marker endpoint
        "latitude": latitude,
        "longitude": longitude,
        "description": description,
        "event_time": event_time,
        "marker_details": {"source_name": source_name, "title": title},
    }

    response = requests.post(url, headers=get_headers(auth_token), json=payload)
    try:
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        print("Marker creation error:", response.text)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Create (upsert) a marker at the final GPS waypoint of a Skydio mission run."
    )
    parser.add_argument(
        "--flight_id",
        required=True,
        help="Flight ID used to fetch mission runs and the associated mission template",
    )
    args = parser.parse_args()

    # 1) Retrieve auth token from environment variable
    auth_token = os.getenv("API_TOKEN")
    if not auth_token:
        print("Error: The API_TOKEN environment variable is not set.")
        sys.exit(1)

    flight_id = args.flight_id

    # 1) Get mission runs for the flight
    mission_runs_response = get_mission_runs_for_flight(flight_id, auth_token)
    print("Mission Runs Response:\n", mission_runs_response)

    mission_runs = mission_runs_response.get("data", {}).get("mission_runs", [])
    if not mission_runs:
        print("No mission runs found for this flight.")
        return

    # Loop over each mission run
    for run in mission_runs:
        run_uuid = run["uuid"]
        template_uuid = run["mission_template_uuid"]
        end_time_str = run.get("end_time")

        # 2) Fallback to now if missing
        if end_time_str:
            event_time = end_time_str
        else:
            event_time = arrow.utcnow().isoformat()

        # 3) Fetch the mission template
        template_resp = get_mission_template_by_id(template_uuid, auth_token)
        print(f"\nMission Template Response (UUID = {template_uuid}):\n", template_resp)

        waypoints = template_resp["data"]["mission_template"].get("waypoints", [])
        if not waypoints:
            print("No waypoints found in the mission template.")
            continue

        # Identify the final waypoint that includes GPS coords
        final_waypoint = waypoints[-1]  # last item
        position = final_waypoint.get("position", {})
        if position.get("frame") != "GPS":
            print(
                "Warning: Final waypoint does not have GPS coordinates. Skipping marker."
            )
            continue

        lat = position["latitude"]
        lon = position["longitude"]

        # 4) Create a marker at that location
        description = f"Marker for mission run {run_uuid} at final waypoint."
        marker_response = upsert_marker(
            auth_token=auth_token,
            latitude=lat,
            longitude=lon,
            description=description,
            event_time=event_time,
        )

        print(f"Created marker for mission run {run_uuid}:\n", marker_response)


if __name__ == "__main__":
    main()
