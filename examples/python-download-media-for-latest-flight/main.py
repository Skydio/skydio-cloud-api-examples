import os
import argparse
import requests

# ----------------- CONFIGURATION ------------------
# Get API token from environment variable
API_TOKEN = os.getenv("API_TOKEN")  # Must be set before running the script
BASE_URL = "https://api.skydio.com/api/v0"


# ----------------- HELPER FUNCTIONS ------------------
def get_headers() -> dict:
    """Get headers for API requests."""
    if not API_TOKEN:
        raise EnvironmentError("API_TOKEN environment variable is not set.")
    return {"Accept": "application/json", "Authorization": f"ApiToken {API_TOKEN}"}


def get_vehicle_by_serial(serial: str) -> dict:
    url = f"{BASE_URL}/vehicle/{serial}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json().get("data", {}).get("vehicle", {})


def get_latest_flight(vehicle_serial: str) -> dict:
    url = f"{BASE_URL}/flights"
    params = {"vehicle_serial": vehicle_serial}
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    flights = response.json().get("data", {}).get("flights", [])
    if not flights:
        raise Exception("No flights found for this vehicle")
    return flights[0]


def get_flight_media(flight_id: str) -> list:
    url = f"{BASE_URL}/media_files"
    params = {"flight_id": flight_id}
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    return response.json().get("data", {}).get("files", [])


def download_file(file_uuid: str, filename: str) -> None:
    url = f"{BASE_URL}/media/download/{file_uuid}"
    response = requests.get(url, stream=True, headers=get_headers())
    response.raise_for_status()
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def delete_file(file_uuid: str) -> dict:
    url = f"{BASE_URL}/media/{file_uuid}/delete"
    response = requests.delete(url, headers=get_headers())
    response.raise_for_status()
    return response.json()


# ----------------- MAIN SCRIPT ------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download media from the most recent Skydio flight"
    )
    parser.add_argument(
        "--vehicle_serial", "-v", help="The serial of the Skydio vehicle", required=True
    )
    parser.add_argument(
        "--output_directory",
        "-o",
        help="The directory where media files will be saved",
        required=True,
    )
    parser.add_argument(
        "--delete-downloaded-files",
        "-d",
        action="store_true",
        help="Delete files from Skydio Cloud after downloading",
    )
    args = parser.parse_args()

    os.makedirs(args.output_directory, exist_ok=True)

    # Make sure the vehicle exists
    print(f"Getting vehicle with serial '{args.vehicle_serial}'...")
    vehicle = get_vehicle_by_serial(args.vehicle_serial)
    if not vehicle:
        print(f"Vehicle with serial '{args.vehicle_serial}' not found.")
        return

    print("Getting most recent flight...")
    flight = get_latest_flight(args.vehicle_serial)
    flight_id = flight["flight_id"]
    print(f"Flight ID: {flight_id} - Started at {flight['takeoff']}")

    print("Fetching media files...")
    media_files = get_flight_media(flight_id)
    if not media_files:
        print("No media files found for this flight.")
        return

    for file in media_files:
        file_uuid = file["uuid"]
        file_name = file.get("filename", f"media_{file_uuid}")
        local_path = os.path.join(args.output_directory, file_name)
        print(f"Downloading {file_name}...")
        download_file(file_uuid, local_path)

        if args.delete_downloaded_files:
            print(f"Deleting {file_name} from Skydio Cloud...")
            delete_file(file_uuid)

    print(f"\nDownload complete! Files saved in '{args.output_directory}'")


if __name__ == "__main__":
    main()
