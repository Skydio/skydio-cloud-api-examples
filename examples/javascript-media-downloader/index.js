const express = require("express");
const axios = require("axios");
const fs = require("fs");
const path = require("path");
const bodyParser = require("body-parser");

// ----------------- CONFIGURATION ------------------
const API_TOKEN = process.env.API_TOKEN || ""; // Set your API token in environment variables
const BASE_URL = "https://api.skydio.com/api/v0";

// ----------------- HELPER FUNCTIONS ------------------
function getHeaders() {
  return {
    Accept: "application/json",
    Authorization: `ApiToken ${API_TOKEN}`,
  };
}

async function getVehicleBySerial(serial) {
  const url = `${BASE_URL}/vehicle/${serial}`;
  const response = await axios.get(url, { headers: getHeaders() });
  return response.data.data.vehicle;
}

async function getLatestFlight(vehicleSerial) {
  const url = `${BASE_URL}/flights`;
  const response = await axios.get(url, {
    headers: getHeaders(),
    params: { vehicle_serial: vehicleSerial },
  });
  const flights = response.data.data.flights;
  if (!flights || flights.length === 0) {
    throw new Error("No flights found for this vehicle");
  }
  return flights[0];
}

async function getFlightMedia(flightId) {
  const url = `${BASE_URL}/media_files`;
  const response = await axios.get(url, {
    headers: getHeaders(),
    params: { flight_id: flightId },
  });
  return response.data.data.files;
}

async function downloadFile(fileUuid, filename) {
  const url = `${BASE_URL}/media/download/${fileUuid}`;
  const response = await axios.get(url, {
    headers: getHeaders(),
    responseType: "stream",
  });
  return new Promise((resolve, reject) => {
    const writer = fs.createWriteStream(filename);
    response.data.pipe(writer);
    writer.on("finish", resolve);
    writer.on("error", reject);
  });
}

async function deleteFile(fileUuid) {
  const url = `${BASE_URL}/media/${fileUuid}/delete`;
  const response = await axios.delete(url, { headers: getHeaders() });
  return response.data;
}

// ----------------- EXPRESS SERVER SETUP ------------------
const app = express();
app.use(bodyParser.json());

// POST /download endpoint
app.post("/download", async (req, res) => {
  try {
    const { vehicle_serial, output_directory, delete_downloaded_files } =
      req.body;
    if (!vehicle_serial || !output_directory) {
      return res
        .status(400)
        .json({ error: "vehicle_serial and output_directory are required" });
    }

    // Ensure output directory exists
    fs.mkdirSync(output_directory, { recursive: true });

    console.log(`Getting vehicle with serial '${vehicle_serial}'...`);
    const vehicle = await getVehicleBySerial(vehicle_serial);
    if (!vehicle) {
      return res
        .status(404)
        .json({ error: `Vehicle with serial '${vehicle_serial}' not found.` });
    }

    console.log("Getting most recent flight...");
    const flight = await getLatestFlight(vehicle_serial);
    const flightId = flight.flight_id;
    console.log(`Flight ID: ${flightId} - Started at ${flight.takeoff}`);

    console.log("Fetching media files...");
    const mediaFiles = await getFlightMedia(flightId);
    if (!mediaFiles || mediaFiles.length === 0) {
      return res
        .status(404)
        .json({ error: "No media files found for this flight." });
    }

    const downloadResults = [];
    for (const file of mediaFiles) {
      const fileUuid = file.uuid;
      const fileName = file.filename || `media_${fileUuid}`;
      const localPath = path.join(output_directory, fileName);
      console.log(`Downloading ${fileName}...`);
      await downloadFile(fileUuid, localPath);
      downloadResults.push({ file: fileName, localPath });

      if (delete_downloaded_files) {
        console.log(`Deleting ${fileName} from Skydio Cloud...`);
        await deleteFile(fileUuid);
      }
    }

    res.json({
      message: `Download complete! Files saved in '${output_directory}'`,
      files: downloadResults,
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 1337;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
