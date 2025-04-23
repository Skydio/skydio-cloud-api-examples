"""
This example demonstrates how to connect to consume a vehicle's live telemetry data after receiving
a Live Stream Status webhook from Skydio. The script uses FastAPI to handle incoming webhook requests
and the `websockets` library to establish a websocket connection to the telemetry stream.

Usage instructions:
1. Set up your environment and install the required packages. See the README for details.

2. Set the following environment variables:
```
export API_TOKEN="your_token_here"
```

 - API_TOKEN: refers to the token secret, which is only visible immediately after creating the token.

3. Start the server:
```
python live_telemetry.py
```

4. Send a webhook to the server to start or stop the websocket connection. You can use the
   live_stream_status_webhook.py script to do this. Make sure that the WEBHOOK_URL is set correctly
   (see below).

Note: we recommend using the demo stream for initial testing. When testing with a simulator or real
vehicle, make sure that the websocket URL is correct by comparing it to the one in the Skydio Cloud UI,
under Settings -> Devices -> Your vehicle -> Connectivity -> Streaming.
"""

from fastapi import FastAPI, Request
import asyncio
import websockets
import json
import os

app = FastAPI()

# Get the API token secret from an environment variable
API_TOKEN_SECRET = os.getenv("API_TOKEN_SECRET")

# Store active websocket tasks per vehicle
active_telemetry_connections = {}


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    event_type = payload.get("event_type")
    if event_type != "skydio.cloud.event.live_stream_status_changed":
        print(f"Unsupported event type: {event_type}")
        return {"status": "ignored"}

    webhook_data = payload.get("data", {}).get("resource", {})
    live_stream_status = webhook_data.get("live_stream_status")
    vehicle_serial = webhook_data.get("vehicle_serial")

    print(f"Received event: {event_type} for vehicle: {vehicle_serial}")
    print(f"Stream status: {live_stream_status}")

    if live_stream_status == "LIVE_STREAM_START":
        if vehicle_serial in active_telemetry_connections:
            print(f"Restarting telemetry connection for {vehicle_serial}")
            active_telemetry_connections[vehicle_serial].cancel()

        ws_url_with_auth = build_ws_url(vehicle_serial)
        task = asyncio.create_task(
            connect_to_telemetry_ws(vehicle_serial, ws_url_with_auth)
        )
        active_telemetry_connections[vehicle_serial] = task

    elif live_stream_status == "LIVE_STREAM_STOP":
        print(f"Stopping telemetry for {vehicle_serial}")
        task = active_telemetry_connections.get(vehicle_serial)
        if task and not task.done():
            task.cancel()
        active_telemetry_connections.pop(vehicle_serial, None)

    return {"status": "received"}


def build_ws_url(vehicle_serial: str):
    """
    Build the websocket URL with the API token and vehicle serial.
    NOTE: When troubleshooting, make sure that this URL is correct by comparing it to the one in the
    Skydio Cloud UI, under Settings -> Devices -> Your vehicle -> Connectivity -> Streaming.
    """
    if not API_TOKEN_SECRET:
        print("API_TOKEN_SECRET is not set. Returning basic URL without token.")
        return f"wss://stream.skydio.com/data/{vehicle_serial}"
    return f"wss://stream.skydio.com/data/{vehicle_serial}?token={API_TOKEN_SECRET}"


async def connect_to_telemetry_ws(vehicle_serial: str, ws_url: str):
    print(f"Connecting to telemetry websocket: {ws_url}")
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"Connected to telemetry for {vehicle_serial}")
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"[{vehicle_serial}] Telemetry:", json.dumps(data, indent=2))
    except asyncio.CancelledError:
        print(f"Telemetry websocket task for {vehicle_serial} was cancelled.")
    except Exception as e:
        print(f"WebSocket error for {vehicle_serial}: {e}")
    finally:
        print(f"Disconnected from telemetry for {vehicle_serial}")


if __name__ == "__main__":
    import uvicorn

    # Runs the webhook server on http://localhost:8001/webhook
    uvicorn.run("live_telemetry:app", host="0.0.0.0", port=8001, reload=True)
