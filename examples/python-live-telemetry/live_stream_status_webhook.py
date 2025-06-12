"""
This script sends a webhook to a local server to start a livestream for a vehicle. Can be used for
testing the rtsp_streaming.py and live_telemetry.py examples.

The URIs correspond to the demo streams mentioned in the RTSP Streaming API Reference, but can be
modified to point to a different RTSP stream if needed.

Usage instructions:

1. Set up your environment and install the required packages. See the README for details.
2. Make sure the WEBHOOK_URL is set to the correct URL of your webhook server. If testing with
   rtsp_streaming.py or live_telemetry.py, make sure that the port is set correctly.
3. Run the script with the desired arguments:

```
python live_stream_status_webhook.py [-optional-arguments]
```

For more full details on accepted arguments, run:
```
python live_stream_status_webhook.py -h
```

Note: we recommend using the demo stream for initial testing. When testing with a simulator or real
vehicle, make sure that the rtsp_url is correct by comparing it to the one in the Skydio Cloud UI,
under Settings -> Devices -> Your vehicle -> Connectivity -> Streaming.
"""

from uuid import uuid4
import argparse
import arrow
import requests

# URL of the webhook server
WEBHOOK_URL = "http://localhost:8000/webhook"


def get_payload(status, stream_type, vehicle_serial):
    if status == "stop":
        live_stream_status = "LIVE_STREAM_STOP"
    else:
        live_stream_status = "LIVE_STREAM_START"

    if vehicle_serial:
        rtsp_url = f"rtsps://stream.skydio.com/{vehicle_serial}/{stream_type}"
    else:
        # Default to demo stream if no vehicle serial is provided
        rtsp_url = f"rtsps://stream.skydio.com/demo/Skydio/{stream_type}"
        vehicle_serial = "demo"

    return {
        "data": {
            "resource": {
                "live_stream_status": live_stream_status,
                "rtsp_url": rtsp_url,
                "stream_type": stream_type,
                "vehicle_serial": vehicle_serial,
            }
        },
        "event_time": arrow.utcnow().isoformat(),  # Current time in ISO format
        "event_type": "skydio.cloud.event.live_stream_status_changed",
        "id": str(uuid4()),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Send a webhook command to the server."
    )

    parser.add_argument(
        "--status",
        "-s",
        type=str,
        choices=["start", "stop"],
        default="start",
        help="Live stream status to send (start, stop). Defaults to start.",
    )

    parser.add_argument(
        "--stream_type",
        "-t",
        type=str,
        choices=["color", "thermal"],
        default="color",
        help="Type of stream to start. Defaults to color.",
    )

    parser.add_argument(
        "--vehicle_serial",
        "-v",
        type=str,
        help="Vehicle serial. If not provided, RTSP url defaults to the demo stream URL.",
    )

    args = parser.parse_args()

    payload = get_payload(args.status, args.stream_type, args.vehicle_serial)

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        print(response)
    except Exception as e:
        print(f"Failed to send POST request: {e}")


if __name__ == "__main__":
    main()
