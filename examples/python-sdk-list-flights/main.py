import csv
import os
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder
import skydio_sdk


def main():
    csv_file = "flights.csv"
    per_page = 10

    configuration = skydio_sdk.Configuration(
        host="https://api.skydio.com/api",
        api_key={"APITokenHeader": os.environ.get("API_TOKEN")},
    )

    with skydio_sdk.ApiClient(configuration) as api_client:
        api_instance = skydio_sdk.FlightsApi(api_client)
        total_flights_exported = 0
        with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=CSV_FIELDNAMES, extrasaction="ignore"
            )
            writer.writeheader()
            for flight_data in iterate_flight_pages(api_instance, per_page):
                flight = skydio_sdk.Flight.from_dict(flight_data)
                row = build_flight_csv_row(flight)
                writer.writerow(row)
                total_flights_exported += 1

        print(f"\nSuccessfully exported {total_flights_exported} flights to {csv_file}")
        return 0


CSV_FIELDNAMES = [
    "flight_id",
    "user_email",
    "has_telemetry",
    "takeoff_time",
    "takeoff_time_local",
    "takeoff_latitude",
    "takeoff_longitude",
    "landing_time",
    "landing_time_local",
    "duration",
    "vehicle_serial",
    "battery_serial",
    "sensor_package_serial",
    "sensor_package_type",
    "attachment_1_serial",
    "attachment_1_type",
    "attachment_1_mount_point",
    "attachment_2_serial",
    "attachment_2_type",
    "attachment_2_mount_point",
    "attachment_3_serial",
    "attachment_3_type",
    "attachment_3_mount_point",
    "attachment_4_serial",
    "attachment_4_type",
    "attachment_4_mount_point",
]


def build_flight_csv_row(flight: skydio_sdk.Flight):

    return {
        "flight_id": flight.flight_id,
        "user_email": flight.user_email,
        "has_telemetry": flight.has_telemetry,
        "takeoff_time": flight.takeoff,
        "takeoff_latitude": flight.takeoff_latitude,
        "takeoff_longitude": flight.takeoff_longitude,
        "takeoff_time_local": utc_to_local(
            flight.takeoff_latitude, flight.takeoff_longitude, flight.takeoff
        ),
        "landing_time": flight.landing,
        "landing_time_local": utc_to_local(
            flight.takeoff_latitude, flight.takeoff_longitude, flight.landing
        ),
        "duration": (
            (
                datetime.fromisoformat(flight.landing)
                - datetime.fromisoformat(flight.takeoff)
            ).total_seconds()
            if flight.takeoff and flight.landing
            else ""
        ),
        "vehicle_serial": flight.vehicle_serial,
        "battery_serial": flight.battery_serial,
        "sensor_package_serial": get_deep(
            flight,
            "sensor_package",
            "sensor_package_serial",
        ),
        "sensor_package_type": get_deep(
            flight,
            "sensor_package",
            "sensor_package_type",
        ),
        "attachment_1_serial": get_deep(flight, "attachments", 0, "attachment_serial"),
        "attachment_1_type": get_deep(flight, "attachments", 0, "attachment_type"),
        "attachment_1_mount_point": get_deep(flight, "attachments", 0, "mount_point"),
        "attachment_2_serial": get_deep(flight, "attachments", 1, "attachment_serial"),
        "attachment_2_type": get_deep(flight, "attachments", 1, "attachment_type"),
        "attachment_2_mount_point": get_deep(flight, "attachments", 1, "mount_point"),
        "attachment_3_serial": get_deep(flight, "attachments", 2, "attachment_serial"),
        "attachment_3_type": get_deep(flight, "attachments", 2, "attachment_type"),
        "attachment_3_mount_point": get_deep(flight, "attachments", 2, "mount_point"),
        "attachment_4_serial": get_deep(flight, "attachments", 3, "attachment_serial"),
        "attachment_4_type": get_deep(flight, "attachments", 3, "attachment_type"),
        "attachment_4_mount_point": get_deep(flight, "attachments", 3, "mount_point"),
    }


def iterate_flight_pages(api_instance: skydio_sdk.FlightsApi, per_page: int):

    page_number = 1
    total_pages = None

    while True:
        print(f"Fetching page {page_number}...")

        api_response = api_instance.flights_get_v0_flights(
            page_number=page_number, per_page=per_page
        )

        flights = api_response.flights if hasattr(api_response, "flights") else []

        if hasattr(api_response, "pagination"):
            pagination = api_response.pagination
            if hasattr(pagination, "total_pages"):
                total_pages = pagination.total_pages
                if page_number == 1:
                    print(f"Total pages: {total_pages}")

        if not flights:
            break

        for flight in flights:
            yield flight

        if total_pages is not None and page_number >= total_pages:
            break
        if total_pages is None and len(flights) < per_page:
            break

        page_number += 1


def utc_to_local(lat, lon, utc_value):
    if utc_value is None or lat is None or lon is None:
        return ""

    try:
        if isinstance(utc_value, str):
            utc_dt = datetime.fromisoformat(utc_value)
        else:
            utc_dt = utc_value

        if utc_dt.tzinfo is None:
            utc_dt = pytz.utc.localize(utc_dt)
        else:
            utc_dt = utc_dt.astimezone(pytz.utc)

        lat_f = float(lat)
        lon_f = float(lon)

        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat_f, lng=lon_f)
        if not tz_name:
            return ""

        local_tz = pytz.timezone(tz_name)
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt.isoformat()
    except (ValueError, pytz.UnknownTimeZoneError, TypeError):
        return ""


def get_deep(root, *path, default: str = "") -> str:
    """Safely navigate nested attributes / dicts / lists, defaulting to an empty string."""

    cur = root
    for key in path:
        if cur is None:
            return default

        if isinstance(key, int):
            if not isinstance(cur, list) or key >= len(cur):
                return default
            cur = cur[key]
            continue

        # key is a string: support both dicts and objects
        if isinstance(cur, dict):
            cur = cur.get(key, default)
        else:
            cur = getattr(cur, key, default)

    return default if cur is None else cur


if __name__ == "__main__":
    exit(main())
