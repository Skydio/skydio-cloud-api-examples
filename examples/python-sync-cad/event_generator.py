import time
import random
from sqlalchemy.orm import Session
from database import SessionLocal, CADEvent

TITLES = [
    "Structure Fire",
    "Medical Emergency",
    "Suspicious Person",
    "Traffic Accident",
    "Noise Complaint"
]
CATEGORIES = ["Fire", "Medical", "Police", "Traffic", "Other"]
DESCRIPTIONS = [
    "A multi-story building is reported to be on fire.",
    "Request for immediate medical assistance for an individual.",
    "An individual is reported to be acting suspiciously in the area.",
    "A multi-vehicle collision has occurred on the main highway.",
    "A public disturbance has been reported by local residents."
]

# San Francisco Bay Area coordinates range
LAT_RANGE = (37.5, 37.9)
LON_RANGE = (-122.5, -122.0)

def create_cad_event(db: Session):
    idx = random.randint(0, len(TITLES) - 1)
    event = CADEvent(
        title=TITLES[idx],
        latitude=random.uniform(*LAT_RANGE),
        longitude=random.uniform(*LON_RANGE),
        description=DESCRIPTIONS[idx],
        category=CATEGORIES[idx]
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    print(f"Created event {event.id}: {event.title}")
    return event

def main():
    print("Starting event generator...")
    db = SessionLocal()
    try:
        while True:
            create_cad_event(db)
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping event generator.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
