# Skydio API Example: Python RTSP Streaming

This example demonstrates how to receive a Live Stream Status webhook from Skydio and connect to a
vehicle's RTSP stream using OpenCV.

## Usage

Follow the instructions in the [README.md](../../README.md) file in the root directory of this repository.

Then run this script with the desired flight ID:

Set the following environment variables:

```bash
# Refers to the token secret, which is only visible immediately after creating the token.
export API_TOKEN="your_token_here"

# In the Skydio Cloud UI, select 'Copy Token ID' on your API token to get this value.
export API_TOKEN_ID="your_token_id_here"

# Optional; If set to "true", uses cv2.imshow to display the stream. If not set or false, runs in headless mode.
export USE_GUI_STREAMING=true
```

Start the server:

```bash
python main.py
```

Send a webhook to the server to start or stop the stream. You can use the `live_stream_status_webhook.py`
script to do this. Make sure that the WEBHOOK_URL is set correctly (see below).

> ℹ️ NOTE: When troubleshooting, make sure that the rtsp_url is correct by comparing it to the one in the
> Skydio Cloud UI, under Settings -> Devices -> Your vehicle -> Connectivity -> Streaming.

> ℹ️ NOTE: This script supports both GUI and headless operation. In GUI mode, it uses cv2.imshow() to display
> the RTSP video stream in a window. This requires a graphical environment (GUI). If you are running the
> script on a headless server (e.g., via SSH, a cloud VM, or a container without display support), enable
> headless mode by omitting the USE_GUI_STREAMING variable or setting it to false.

To run the script in headless mode, set `USE_GUI_STREAMING=false` or omit it. The headless function will also
retry connection attempts if the stream fails or drops unexpectedly.
