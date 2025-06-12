from fastapi import FastAPI, Request
from urllib.parse import urlparse, urlunparse
import threading
import cv2
import time
import uvicorn
import os

app = FastAPI()

# Get credentials from environment variables
api_token = os.getenv("API_TOKEN")
api_token_id = os.getenv("API_TOKEN_ID")

# Track stream threads and stop signals per vehicle
active_streams = {}  # vehicle_serial: {"thread": Thread, "stop_event": Event}

# Toggle GUI mode (True = use cv2.imshow, False = headless)
USE_GUI_STREAMING = os.getenv("USE_GUI_STREAMING", "false").lower() == "true"


@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()

    event_type = payload.get("event_type")
    if event_type != "skydio.cloud.event.live_stream_status_changed":
        print(f"Unsupported event type: {event_type}")
        return {"status": "ignored"}

    webhook_data = payload.get("data", {}).get("resource", {})
    live_stream_status = webhook_data.get("live_stream_status")
    rtsp_url = webhook_data.get("rtsp_url")
    stream_type = webhook_data.get("stream_type")
    vehicle_serial = webhook_data.get("vehicle_serial")

    print(f"Received event: {event_type} for vehicle: {vehicle_serial}")
    print(f"Stream status: {live_stream_status}, stream type: {stream_type}")

    if live_stream_status == "LIVE_STREAM_START" and rtsp_url:
        print(f"RTSP Stream Available at: {rtsp_url}")
        stream_url_with_creds = parse_stream_url_and_inject_credentials(rtsp_url)

        # Start new stream and store task
        if vehicle_serial in active_streams:
            print(f"Stopping existing stream for {vehicle_serial}")
            active_streams[vehicle_serial]["stop_event"].set()
            active_streams[vehicle_serial]["thread"].join()
            active_streams.pop(vehicle_serial)

        stop_event = threading.Event()
        thread = threading.Thread(
            target=start_stream_gui if USE_GUI_STREAMING else start_stream_headless,
            args=(stream_url_with_creds, stop_event),
        )
        thread.start()

        active_streams[vehicle_serial] = {"thread": thread, "stop_event": stop_event}

    elif live_stream_status == "LIVE_STREAM_STOP":
        print(f"Stopping stream for vehicle: {vehicle_serial}")
        stream_info = active_streams.get(vehicle_serial)
        if stream_info:
            stream_info["stop_event"].set()
            stream_info["thread"].join()
            print(f"Stream for {vehicle_serial} canceled.")
            active_streams.pop(vehicle_serial)
        else:
            print(f"No active stream found for {vehicle_serial}")

    return {"status": "received"}


def parse_stream_url_and_inject_credentials(rtsp_url: str):
    """
    Parses the RTSP URL and injects the API token and token ID into the netloc.
    This is necessary to authenticate with the Skydio Cloud API when accessing the RTSP stream for
    a vehicle or simulator (not the demo stream).
    Input: rtsps://stream.skydio.com/<skydio_serial>/<stream_name>
    Output: rtsps://<api_token_id>:<api_token_secret>@stream.skydio.com/<skydio_serial>/<stream_name>
    """
    if not api_token or not api_token_id:
        print("API token or token ID is missing. Returning original RTSP URL.")
        return rtsp_url

    parsed = urlparse(rtsp_url)
    netloc_with_credentials = f"{api_token_id}:{api_token}@{parsed.netloc}"
    return urlunparse(parsed._replace(netloc=netloc_with_credentials))


def start_stream_gui(rtsp_url: str, stop_event: threading.Event, max_retries: int = 5):
    """
    Connects to the RTSP stream and displays it using OpenCV GUI (cv2.imshow).
    Automatically retries on failure.
    """
    retries = 0
    while retries < max_retries and not stop_event.is_set():
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            print("Failed to open RTSP stream. Retrying...")
            retries += 1
            time.sleep(2)
            continue

        print("Opening RTSP stream (GUI)...")
        while cap.isOpened() and not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from RTSP stream.")
                break

            cv2.imshow("Skydio RTSP Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("User requested stop (pressed 'q').")
                stop_event.set()
                break

        cap.release()
        cv2.destroyAllWindows()
        if not stop_event.is_set():
            print("Stream closed unexpectedly. Retrying...")
            retries += 1
            time.sleep(2)
        else:
            break

    if retries >= max_retries:
        print("Maximum retries reached. Giving up on stream.")


def start_stream_headless(
    rtsp_url: str, stop_event: threading.Event, max_retries: int = 5
):
    """
    Connects to the RTSP stream and processes frames in headless mode (no GUI).
    Runs continuously until cancelled externally (via webhook).
    Automatically retries on failure.
    """
    retries = 0
    while retries < max_retries and not stop_event.is_set():
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            print("Failed to open RTSP stream. Retrying...")
            retries += 1
            time.sleep(2)
            continue

        print("Streaming frames (headless mode)...")
        frame_count = 0

        while cap.isOpened() and not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from RTSP stream.")
                break

            frame_count += 1
            if frame_count % 30 == 0:
                print(f"Processed {frame_count} frames...")

        cap.release()
        if not stop_event.is_set():
            print("Stream closed unexpectedly. Retrying...")
            retries += 1
            time.sleep(2)
        else:
            break

    print("Headless stream closed after", frame_count, "frames.")
    if retries >= max_retries:
        print("Maximum retries reached. Giving up on stream.")


if __name__ == "__main__":
    # Runs the webhook server on http://localhost:8000/webhook
    uvicorn.run("rtsp_streaming:app", host="0.0.0.0", port=8000, reload=True)
