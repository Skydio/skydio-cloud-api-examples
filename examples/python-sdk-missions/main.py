# Skydio Mission SDK Example
#
# Usage:
#   python main.py simple_waypoints.json --upload
#   python main.py simple_waypoints.json -o my_mission.json
#
# See geo.py for coordinate system reference and geodetic primitives.
# See mission_helpers.py for mission building functions.

import argparse
import json
import os

from mission_helpers import build_mission


def main():
    parser = argparse.ArgumentParser(
        description="Skydio API - Mission SDK example. Create a waypoint mission from a JSON file."
    )
    parser.add_argument(
        "waypoints_file", help="Path to JSON file containing waypoints"
    )
    parser.add_argument(
        "-o", "--output-mission",
        help="Output file path for the generated mission JSON",
    )
    parser.add_argument(
        "--output-body",
        help="Output file path for the full API request body JSON",
    )
    parser.add_argument(
        "--output-curl-sh",
        help="Output file path for a curl command shell script",
    )
    parser.add_argument(
        "--upload", action="store_true", help="Upload the mission to the Skydio API"
    )
    args = parser.parse_args()

    # Read waypoints from JSON file
    with open(args.waypoints_file, "r") as f:
        waypoints = json.load(f)

    print(f"Loaded {len(waypoints)} waypoints from {args.waypoints_file}")

    # Build mission (requires SDK)
    try:
        mission = build_mission(waypoints, name="Waypoint Mission")
    except ImportError as e:
        print(f"Error: {e}")
        return
    
    print("Created mission with waypoint sequences")
    print(f"Mission display name: {mission.display_name}")

    # Save mission to JSON file if output-mission is specified
    if args.output_mission:
        mission_dict = mission.to_dict()
        with open(args.output_mission, "w") as f:
            json.dump(mission_dict, f, indent=2)
        print(f"Saved mission to {args.output_mission}")

    # Build the full request body (needed for --output-body, --output-curl-sh, and --upload)
    if args.output_body or args.output_curl_sh or args.upload:
        # Deferred import - only needed for upload/body operations
        try:
            from skydio_client.models import (
                Oyuk2Ny7392O85U5MissionsPostV1MissionDocumentTemplateBody as MissionTemplateBody,
                Oyuk2Ny7392O85U5MissionsPostV1MissionDocumentTemplateBodyVehicleContext as VehicleContext,
            )
        except ImportError as e:
            print(f"Error: SDK not available. Run 'python generate_sdk.py' first.\n{e}")
            return
        
        vehicle_context = VehicleContext(vehicle_class="Skydio X10")
        body = MissionTemplateBody(
            mission_template=mission,
            vehicle_context=vehicle_context,
        )
        body_dict = body.to_dict()

        # Save request body to file if specified
        if args.output_body:
            with open(args.output_body, "w") as f:
                json.dump(body_dict, f, indent=2)
            print(f"Saved request body to {args.output_body}")

        # Save curl command to file if specified
        if args.output_curl_sh:
            curl_script = f"""#!/bin/bash
# Curl command to upload mission to Skydio API
# Usage: ./{args.output_curl_sh}
# Requires API_TOKEN environment variable to be set

curl -X POST "https://api.skydio.com/api/v1/mission_document/template" \\
  -H "Authorization: $API_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(body_dict)}'
"""
            with open(args.output_curl_sh, "w") as f:
                f.write(curl_script)
            print(f"Saved curl script to {args.output_curl_sh}")

        # Upload to API if requested
        if args.upload:
            print("\nUploading mission to Skydio API...")
            api_token = os.environ.get("API_TOKEN")
            if not api_token:
                print("Error: API_TOKEN environment variable not set")
                return

            try:
                from skydio_client.client import AuthenticatedClient
            except ImportError as e:
                print(f"Error: SDK not available. Run 'python generate_sdk.py' first.\n{e}")
                return

            client = AuthenticatedClient(
                base_url="https://api.skydio.com/api",
                token=api_token,
                prefix="",  # Skydio API uses token directly without Bearer prefix
            )

            with client:
                # Use raw HTTP - SDK response parsing doesn't handle API's response envelope
                httpx_client = client.get_httpx_client()
                response = httpx_client.post(
                    "/v1/mission_document/template",
                    json=body_dict,
                    headers={"Content-Type": "application/json"},
                )
                print(f"\nResponse status: {response.status_code}")
                response_data = response.json()
                if (
                    response.status_code == 200
                    and response_data.get("skydio_error_code") == 0
                ):
                    mission_template = response_data.get("data", {}).get(
                        "missionTemplate", {}
                    )
                    print("Mission uploaded successfully!")
                    print(f"  Display Name: {mission_template.get('displayName')}")
                    print(f"  Template UUID: {mission_template.get('templateUuid')}")
                else:
                    print(f"Error: {response_data.get('error_message', response.content)}")


if __name__ == "__main__":
    main()
