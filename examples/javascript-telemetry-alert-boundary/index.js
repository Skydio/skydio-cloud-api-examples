const config = require("./config");
const { loadGeoJSON } = require("./geojson");
const { buildWsUrl } = require("./websocket-utils");
const { connectToTelemetryWs } = require("./websocket");
const { getVehicles, getActiveVehicles } = require("./vehicles");

// Track active WebSocket connections by vehicle serial
const activeConnections = new Map();

/**
 * Update WebSocket connections based on current vehicle states
 */
async function updateConnections() {
  try {
    const allVehicles = await getVehicles();
    const activeVehicles = getActiveVehicles(allVehicles);

    const activeSerials = new Set(activeVehicles.map((v) => v.vehicle_serial));

    if (config.DEBUG) {
      console.log(`\n[DEBUG] Polling vehicles - Found ${allVehicles.length} total, ${activeVehicles.length} active (PREP/FLYING)`);
      activeVehicles.forEach((v) => {
        console.log(`  - ${v.vehicle_serial} (${v.name || "unnamed"}): ${v.flight_status}`);
      });
    }

    // Close connections for vehicles that are no longer active
    for (const [serial, ws] of activeConnections.entries()) {
      if (!activeSerials.has(serial)) {
        console.log(`\n🛬 [${serial}] Drone is not flying anymore`);
        if (ws.readyState === 1) {
          ws.close();
        }
        activeConnections.delete(serial);
      }
    }

    // Create connections for new active vehicles
    for (const vehicle of activeVehicles) {
      if (!activeConnections.has(vehicle.vehicle_serial)) {
        console.log(`\n🛫 [${vehicle.vehicle_serial}] Drone is now flying (${vehicle.name || "unnamed"})`);
        const wsUrl = buildWsUrl(vehicle.vehicle_serial);
        const ws = connectToTelemetryWs(vehicle.vehicle_serial, wsUrl, config.DEBUG);
        activeConnections.set(vehicle.vehicle_serial, ws);
      }
    }
  } catch (error) {
    console.error("Error updating connections:", error.message);
  }
}

// ----------------- MAIN FUNCTION ------------------
async function main() {
  if (!config.API_TOKEN_SECRET) {
    console.error("Error: API_TOKEN_SECRET environment variable is not set");
    console.log("\nUsage:");
    console.log("  export API_TOKEN_SECRET=your_api_token");
    console.log("  export GEOJSON_FILE=path/to/boundaries.geojson");
    console.log("  npm start");
    console.log("\nOr:");
    console.log("  node index.js path/to/boundaries.geojson");
    process.exit(1);
  }

  if (!config.GEOJSON_FILE) {
    console.error("Error: GEOJSON_FILE environment variable or file argument not provided");
    console.log("\nUsage:");
    console.log("  export GEOJSON_FILE=path/to/boundaries.geojson");
    console.log("  npm start");
    console.log("\nOr:");
    console.log("  node index.js path/to/boundaries.geojson");
    process.exit(1);
  }

  // Load GeoJSON polygons
  loadGeoJSON(config.GEOJSON_FILE);

  console.log("\n🚁 Starting vehicle monitoring...");
  console.log(`   Polling vehicles every ${config.POLL_INTERVAL_MS / 1000} seconds`);
  console.log(`   Monitoring vehicles in PREPARATION or FLYING state`);

  // Initial poll
  await updateConnections();

  // Set up polling interval
  setInterval(updateConnections, config.POLL_INTERVAL_MS);
}

// Run the main function
main();
