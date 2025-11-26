# Skydio API Example: List Flights using a Python SDK

This project demonstrates how to:

- Generate a Python SDK from the Skydio API (`generate_sdk.py`)
- Use the SDK to build a script that lists flights and exports them to a CSV file
- Compute derived fields such as local time for the flight and flight duration

Note: This example uses a generated Skydio SDK, but it would also be doable without SDK, just using basic HTTP requests and JSON parsing.

## Setup

Generate the SDK (once).

You will need a recent Java version to be installed on your system for this step.

```bash
export API_TOKEN=<YOUR_SKYDIO_API_TOKEN>
python generate_sdk.py
```

## Usage

Run this script

```bash
export API_TOKEN=<YOUR_SKYDIO_API_TOKEN>
python main.py
```
