# Skydio API Example: Python Set Marker at Mission Execution Final Waypoint

This script demonstrates how to:

1. Fetch mission runs associated with a given flight ID using the Skydio API.
2. For each mission run, retrieve the corresponding Mission Template.
3. Identify the final waypoint in the mission template that has GPS coordinates.
4. Create (upsert) a marker at that final waypoint's location using the Skydio API,
   so it appears in Remote Flight Deck for DFR Command customers.

## Usage

Follow the instructions in the [README.md](../../README.md) file in the root directory of this repository.

Then run this script with the desired flight ID:

```bash
python main.py --flight_id <YOUR_FLIGHT_ID>
```
