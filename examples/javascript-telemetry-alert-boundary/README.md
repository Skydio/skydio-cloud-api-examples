# Skydio API Example: Telemetry Alert Boundary

This script automatically monitors all Skydio vehicles in your organization that are in PREP or FLYING state. It polls the vehicles endpoint every minute and connects to each active vehicle's telemetry stream. When a drone enters or leaves predefined geographic boundary polygons, it triggers alerts. It uses GeoJSON files to define alert zones and logs events to the console.

## Prerequisites

1. A Skydio API token with access to vehicle telemetry and vehicle listing
2. The API token must have `vehicle:read` or `vehicle:*` scope
3. A GeoJSON file containing one or more Polygon or MultiPolygon features

## GeoJSON File Format

Create a GeoJSON file with polygon boundaries. You can easily create and visualize GeoJSON polygons using [geojson.io](https://geojson.io) - just draw your polygons on the map and export the GeoJSON.

Example GeoJSON file:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "zone-1",
        "name": "Restricted Area",
        "description": "No-fly zone"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [-122.4194, 37.7749],
            [-122.4094, 37.7749],
            [-122.4094, 37.7849],
            [-122.4194, 37.7849],
            [-122.4194, 37.7749]
          ]
        ]
      }
    }
  ]
}
```

**Note:** GeoJSON coordinates are in `[longitude, latitude]` format.

## Usage

Follow the instructions in the [README.md](../../README.md) file in the root directory of this repository.

Then install dependencies:

```bash
npm install
```

Set your environment variables:

```bash
export API_TOKEN_SECRET="your_api_token_here"
export GEOJSON_FILE="boundaries.geojson"
```

Run the script:

```bash
npm start
```

Or pass the GeoJSON file as a command-line argument:

```bash
node index.js boundaries.geojson
```

### Optional Configuration

You can customize the polling interval (default is 60 seconds):

```bash
export POLL_INTERVAL_MS=10000  # Poll every 10 seconds
```

### Debug Mode

If you're experiencing connection issues or want to see detailed telemetry data, enable debug mode:

```bash
export DEBUG=true
npm start
```

Debug mode will show:

- Full API token information (first/last 10 characters)
- Complete WebSocket URL
- Raw telemetry data for each message
- Position data extraction details
- Full error stack traces

### Development Mode with Nodemon

For easier development, this project includes [nodemon](https://nodemon.io/) which automatically restarts the script when you make changes.

Run in development mode with:

```bash
npm run dev
```

## How It Works

1. The script loads the GeoJSON file and extracts all polygon features
2. It polls the Skydio Cloud API `/api/v0/vehicles` endpoint every minute (configurable)
3. For each vehicle in **PREP** or **FLYING** state:
   - It automatically connects to the vehicle's telemetry WebSocket stream
   - When a vehicle's state changes to something other than PREP/FLYING, the connection is closed
4. For each telemetry message containing position data (latitude/longitude):
   - It checks if the drone is inside any of the defined polygons
   - When the drone **enters** a polygon, it logs: `🟢 ENTERED "Polygon Name"`
   - When the drone **leaves** a polygon, it logs: `🔴 LEFT "Polygon Name"`
5. The script automatically manages connections - connecting to new active vehicles and disconnecting from vehicles that are no longer active

## Example Output

```
export API_TOKEN_SECRET="your_api_token_here"
node index.js boundaries.geojson

🗺️  Loading GeoJSON file: boundaries.geojson
   Found 2 polygon(s)
   - Restricted Area 1 (restricted-zone-1)
   - Authorized Flight Zone (safe-zone-1)

🚁 Starting vehicle monitoring...
   Polling vehicles every 10 seconds
   Monitoring vehicles in PREPARATION or FLYING state

🛫 [sim-2yya984x] Drone is now flying (simFeb5)
   Connecting to telemetry stream...
   ✓ Connected, listening for telemetry...

🟢 [sim-2yya984x] ENTERED "Authorized Flight Zone"
   Location: [37.776650, -122.406374]
   Polygon:  safe-zone-1
   Severity: low

🔴 [sim-2yya984x] LEFT "Authorized Flight Zone"
   Location: [37.776642, -122.406365]
   Polygon:  safe-zone-1
   Severity: low

🛬 [sim-2yya984x] Drone is not flying anymore
   ✗ Disconnected (code=1006)

```
