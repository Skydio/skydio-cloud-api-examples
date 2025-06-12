# Skydio API Example: Javascript Media Downloader

This project provides a Node.js Express server that replicates the functionality of the original Python script `download_media_for_latest_flight.py`. The server exposes a POST endpoint (`/download`) that:

- Retrieves a vehicle by its serial number.
- Fetches the most recent flight for the vehicle.
- Downloads media files associated with that flight.
- Optionally deletes the downloaded media files from Skydio Cloud.

## Usage

Follow the instructions in the [README.md](../../README.md) file in the root directory of this repository.

Then run this script with the desired flight ID: Run the script with the desired arguments:

```bash
npm run start
```

This command will launch the server on port 1337 (or the port specified in the `PORT` environment variable).

### Development Mode with Nodemon

For easier development, this project includes [nodemon](https://nodemon.io/) which automatically restarts the server when you make changes.

Run the server in development mode with:

```bash
npm run dev
```

## API Usage

### Endpoint

`POST /download`

### Request Body

Send a JSON payload with the following keys:

- `vehicle_serial` (string, required): The serial number of the Skydio vehicle.
- `output_directory` (string, required): The directory where media files will be saved.
- `delete_downloaded_files` (boolean, optional): Whether to delete the files from Skydio Cloud after downloading.

### Example Request

```bash
curl -X POST http://localhost:1337/download \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_serial": "YOUR_VEHICLE_SERIAL",
    "output_directory": "./downloads",
    "delete_downloaded_files": false
  }'
```
