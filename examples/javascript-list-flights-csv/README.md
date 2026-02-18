# Skydio API Example: List Flights as CSV

This script fetches flights from the Skydio Cloud API (`GET /v0/flights`), paginates through results 50 at a time, and exports them to a `flights.csv` file.

An optional ISO date argument filters flights to only those since that date.

## Setup

Follow the instructions in the [README.md](../../README.md) file in the root directory of this repository.

Install dependencies:

```bash
npm install
```

## Usage

```bash
export API_TOKEN_SECRET=<YOUR_SKYDIO_API_TOKEN>
node index.js [SINCE_ISO_DATE]
```

Examples:

```bash
# Export all flights
node index.js

# Export flights since a specific date
node index.js 2025-01-01T00:00:00Z
```

## Output

The script writes a `flights.csv` file with the following columns:

| Column              | Description                                     |
| ------------------- | ----------------------------------------------- |
| `flight_id`         | Unique flight identifier                        |
| `incident_id`       | Associated incident identifier (if any)         |
| `pilot_email`       | Email of the pilot who flew                     |
| `takeoff_time`      | Takeoff timestamp (ISO 8601, rounded to second) |
| `landing_time`      | Landing timestamp (ISO 8601, rounded to second) |
| `takeoff_latitude`  | Takeoff latitude                                |
| `takeoff_longitude` | Takeoff longitude                               |
| `duration`          | Flight duration in seconds                      |
| `sensor_package`    | Type of sensor package used                     |
| `attachments`       | Attachment types joined with `+`                |

### Example output

| flight_id | incident_id | pilot_email      | takeoff_time             | landing_time             | takeoff_latitude | takeoff_longitude | duration | sensor_package | attachments        |
| --------- | ----------- | ---------------- | ------------------------ | ------------------------ | ---------------- | ----------------- | -------- | -------------- | ------------------ |
| abc-123   |             | john@example.com | 2025-06-10T14:30:00.000Z | 2025-06-10T14:45:00.000Z | 37.7749          | -122.4194         | 900      | visual         | NightSense+Speaker |
| def-456   | inc-789     | jane@example.com | 2025-06-11T09:00:00.000Z | 2025-06-11T09:12:00.000Z | 34.0522          | -118.2437         | 720      | thermal        |                    |
