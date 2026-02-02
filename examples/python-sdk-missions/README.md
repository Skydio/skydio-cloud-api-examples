# Skydio API Example: Mission SDK

This project demonstrates how to:

- Generate a Python SDK from the Skydio OpenAPI specification
- Create waypoint missions programmatically using the SDK
- Upload missions to the Skydio Cloud API

## File Structure

| File | Purpose | Requires SDK? |
|------|---------|---------------|
| `geo.py` | Geodetic primitives (GpsPoint, LocalFrame, make_waypoint, heading calculations) | No |
| `mission_helpers.py` | Build Skydio Mission objects from waypoints | Yes |
| `main.py` | CLI to build and upload missions from JSON | Yes |
| `generate_sdk.py` | Generate the Skydio SDK from OpenAPI spec | No |
| `skydio_client` | Symlink to generated SDK (broken until you run `generate_sdk.py`) | N/A |

## Quick Start

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install certifi (required for SDK generation on macOS)
pip install --upgrade pip certifi

# 3. Generate the SDK
export API_TOKEN=<YOUR_SKYDIO_API_TOKEN>
python generate_sdk.py

# 4. Install the generated SDK (includes httpx, attrs, python-dateutil)
pip install -e skydio_sdk_generated/skydio-client
pip install requests  # For terrain elevation lookup

# 5. Build and upload a mission
python main.py simple_waypoints.json --upload
```

> **Note**: The `skydio_client` symlink will be broken until you run step 3.

## Usage

### From JSON waypoints file

```bash
python main.py <waypoints_file> -o <output_file> --upload
```

Example:

```bash
python main.py simple_waypoints.json -o mission.json --upload
```

### CLI Options

- `-o, --output-mission <file>`: Save the generated mission JSON to a file
- `--output-body <file>`: Save the full API request body to a file
- `--output-curl-sh <file>`: Generate a curl command script
- `--upload`: Upload the mission directly to the Skydio API

## Waypoint Format

See `simple_waypoints.json` for the expected input format:

```json
{
  "latitude_deg": 37.7897,
  "longitude_deg": -122.3972,
  "altitude_m": 100,
  "heading_deg": 90,
  "pitch_deg": -15,
  "speed_mps": 5,
  "photo": true
}
```

- `heading_deg`: ENU convention (0=East, 90=North, 180=West, 270=South)
- `pitch_deg`: Gimbal pitch (0=level, +90=down)
- `altitude_m`: Meters above takeoff (barometer-based)

## Using with AI Agents

This SDK provides geodetic primitives in `geo.py` that AI agents can use to generate complex flight patterns programmatically.

### Recommended Workflow for AI Agents

```python
from geo import GpsPoint, LocalFrame, EnuPoint, make_waypoint
import math

# 1. Define target
target = GpsPoint(lat=37.7897, lon=-122.3972, alt=0)
frame = LocalFrame(target)

# 2. Generate waypoints with math
waypoints = []
for i in range(36):
    angle = math.radians(i * 10)
    enu = EnuPoint(east=80*math.cos(angle), north=80*math.sin(angle), up=100)
    gps = frame.enu_to_gps(enu)
    # look_at auto-computes heading and pitch to face target
    waypoints.append(make_waypoint(position=gps, look_at=target, photo=True))

# 3. Save waypoints (works without SDK - waypoints are just dicts)
import json
with open("waypoints.json", "w") as f:
    json.dump(waypoints, f, indent=2)

# 4. Build mission (requires SDK)
from mission_helpers import build_mission
mission = build_mission(waypoints, name="Orbit Mission")
```

### Key Primitives in geo.py

| Primitive | Purpose |
|-----------|---------|
| `GpsPoint(lat, lon, alt)` | GPS coordinates (WGS84) |
| `EnuPoint(east, north, up)` | Local meters from origin |
| `LocalFrame(origin)` | Convert between GPS ↔ ENU |
| `make_waypoint(position, look_at, ...)` | Create waypoint dict, auto-computes heading/pitch |
| `heading_between(from_gps, to_gps)` | Compute ENU heading |
| `pitch_to_target(from_gps, to_gps)` | Compute gimbal pitch |
| `compass_to_enu(deg)` / `enu_to_compass(deg)` | Heading conversion |

### Coordinate System Reference

**ENU Heading** (different from compass!):
- 0° = East
- 90° = North
- 180° = West
- 270° = South

**Gimbal Pitch**:
- +90° = Straight down
- 0° = Level (horizon)
- -90° = Straight up

**Conversion**: `enu_deg = (90 - compass_deg) % 360`

### Example Prompt for AI Agents

> "Create a spiral inspection mission around a building at GPS coordinates (37.7897, -122.3972).
> 
> Requirements:
> - Use geo.py primitives (GpsPoint, LocalFrame, make_waypoint)
> - Spiral from 50m to 200m altitude
> - 60 waypoints, 3 full rotations
> - Radius: 80m from center
> - Camera always pointing at the building (use look_at)
> - Take a photo every 3rd waypoint
> 
> Generate the waypoints and save to JSON."

## Troubleshooting

### SSL Certificate Error on macOS

If you see `CERTIFICATE_VERIFY_FAILED` when running `generate_sdk.py`:

```bash
pip install --upgrade certifi
```

The SDK generator uses certifi's CA bundle for SSL verification. This is automatically installed, but if you have issues, ensure it's up to date.

### Old pip version

If you see errors about `pyproject.toml` when installing the generated SDK:

```bash
pip install --upgrade pip
pip install -e skydio_sdk_generated/skydio-client
```

### Missing dependencies

The generated SDK requires these packages (installed automatically):
- `httpx` - HTTP client
- `attrs` - Data classes
- `python-dateutil` - Date parsing

For mission upload functionality, you also need:
- `requests` - Used for terrain elevation lookup
