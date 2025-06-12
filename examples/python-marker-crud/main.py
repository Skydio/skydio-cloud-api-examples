import os
import sys
import json
import argparse
from uuid import uuid4
import arrow
from .skydio_api_client import SkydioAPIClient


def main():
    # Get API token from environment variable
    api_token = os.getenv("API_TOKEN")
    if not api_token:
        sys.exit(
            "Error: API_TOKEN environment variable is not set. Please export it before running this script."
        )

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Skydio Marker CRUD Example")
    parser.add_argument(
        "--generate-uuid",
        action="store_true",
        help="Generate a UUID for the created Marker locally instead of letting Skydio generate it.",
    )
    args = parser.parse_args()

    # Decide whether to generate a marker ID
    marker_id = str(uuid4()) if args.generate_uuid else None

    # Initialize the client
    client = SkydioAPIClient(api_token=api_token)

    # Step 1: Create a marker
    event_time = arrow.now().shift(minutes=-15).isoformat()
    create_payload = {
        "title": "A car robbery in San Mateo, CA",
        "description": "Suspect seen driving a blue sedan",
        "event_time": event_time,
        "latitude": 37.543,
        "longitude": -122.3312,
        "type": "INCIDENT",
    }

    if marker_id:
        create_payload["uuid"] = marker_id

    print(
        f"Creating marker {'with ID ' + marker_id if marker_id else 'with server-generated ID'}"
    )
    response = client.post("/v0/marker", json=create_payload)

    if not marker_id:
        marker_id = response["data"]["marker"]["uuid"]

    print(json.dumps(response, indent=2))

    # Step 2: Fetch list of markers
    query_params = {"per_page": 5, "page": 1}
    response = client.get("/v0/markers", params=query_params)
    print(json.dumps(response, indent=2))

    # Step 3: Update the marker
    update_payload = {
        "uuid": marker_id,
        "title": "A car robbery in San Mateo, CA",
        "description": "Suspect seen driving a blue sedan",
        "event_time": event_time,
        "latitude": 37.543,
        "longitude": -122.3312,
        "type": "INCIDENT",
        "marker_details": {
            "code": "INC",
            "incident_id": "INC-123",
        },
    }

    print(f"\nUpdating marker: {marker_id}")
    response = client.post("/v0/marker", json=update_payload)
    print(json.dumps(response, indent=2))

    # Step 4: Fetch the marker by UUID
    response = client.get(f"/v0/marker/{marker_id}")
    print(f"Fetched marker: {json.dumps(response, indent=2)}")

    # Step 5: Delete the marker
    print(f"\nDeleting marker: {marker_id}")
    response = client.delete(f"/v0/marker/{marker_id}/delete")
    print("Delete response:", response)


if __name__ == "__main__":
    main()
