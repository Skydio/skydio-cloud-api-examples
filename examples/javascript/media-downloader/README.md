# Skydio API Media Downloader

This project provides a Node.js Express server that replicates the functionality of the original Python script `download_media_for_latest_flight.py`. The server exposes a POST endpoint (`/download`) that:

- Retrieves a vehicle by its serial number.
- Fetches the most recent flight for the vehicle.
- Downloads media files associated with that flight.
- Optionally deletes the downloaded media files from Skydio Cloud.

## Prerequisites

- [Node.js](https://nodejs.org/) (version 12 or higher)
- [npm](https://www.npmjs.com/)

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://your-repository-url.git
   cd your-repository-folder
   ```

2. **Install dependencies:**

   ```bash
   npm install
   ```

3. **Set your API token:**

   The API token should be set as an environment variable. You can either export it directly in your terminal or create a `.env` file (if you're using a package like `dotenv`).

   ```bash
   export API_TOKEN=your_api_token_here
   ```

## Running the Server

### Production Mode

Start the server with:

```bash
npm start
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
