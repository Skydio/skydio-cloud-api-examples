# Skydio API Example: Python Live Telemetry

This example demonstrates how to connect to consume a vehicle's live telemetry data after receiving
a Live Stream Status webhook from Skydio. The script uses FastAPI to handle incoming webhook requests
and the `websockets` library to establish a websocket connection to the telemetry stream.

## Usage

Follow the instructions in the [README.md](../../README.md) file in the root directory of this repository.

Then run this script

```bash
python main.py
```

Send a webhook to the server to start or stop the websocket connection. You can use the `live_stream_status_webhook.py` script to do this. Make sure that the WEBHOOK_URL is set correctly (see below).

> ℹ️ NOTE: we recommend using the demo stream for initial testing. When testing with a simulator or real
> vehicle, make sure that the websocket URL is correct by comparing it to the one in the Skydio Cloud UI,
> under Settings -> Devices -> Your vehicle -> Connectivity -> Streaming.
