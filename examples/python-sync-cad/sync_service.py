import os
import time
import requests
import arrow
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import cast
from sqlalchemy.orm import Session
from database import SessionLocal, CADEvent

load_dotenv()  # Load environment variables from .env file

SKYDIO_API_KEY = os.getenv("SKYDIO_API_KEY")
SKYDIO_API_URL = os.getenv("SKYDIO_API_URL", "https://api.skydio.com/v1")

if not SKYDIO_API_KEY:
    raise ValueError("SKYDIO_API_KEY must be set in the .env file.")

HEADERS = {
    "Authorization": SKYDIO_API_KEY,
    "accept": "application/json",
    "Content-Type": "application/json",
}


def get_new_events(db: Session, last_synced: datetime):
    return (
        db.query(CADEvent)
        .filter(CADEvent.event_time > last_synced)
        .order_by(CADEvent.event_time)
        .all()
    )


def create_skydio_marker(event: CADEvent):
    # The marker-crud example uses /v0, but the .env default is /v1. We will use the default from the .env.
    url = f"{SKYDIO_API_URL}/marker"
    payload = {
        "title": event.title,
        "description": event.description,
        "event_time": arrow.get(cast(datetime, event.event_time)).isoformat(),
        "latitude": event.latitude,
        "longitude": event.longitude,
        "type": event.type,
        "marker_details": {
            "code": event.category[:3].upper(),
            "incident_id": f"CAD-{event.id}",
        },
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        json_response = response.json()
        if "error" in json_response:
            print(f"API Error for event {event.id}: {json_response['error']['msg']}")
            return False

        print(f"Successfully created Skydio marker for event {event.id}.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error creating Skydio marker for event {event.id}: {e}")
        return False


def main():
    print("Starting sync service...")
    db = SessionLocal()
    last_synced = datetime.now(timezone.utc)
    print(f"Starting sync from timestamp: {last_synced.isoformat()}")
    try:
        while True:
            events_to_sync = get_new_events(db, last_synced)
            if not events_to_sync:
                print("No new events to sync. Waiting...")
            else:
                for event in events_to_sync:
                    print(f"Syncing event {event.id} created at {event.event_time}...")
                    if create_skydio_marker(event):
                        # Update the cursor to the timestamp of the last successfully synced event
                        last_synced = event.event_time
            time.sleep(2)  # Check for new events every 10 seconds
    except KeyboardInterrupt:
        print("\nStopping sync service.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
