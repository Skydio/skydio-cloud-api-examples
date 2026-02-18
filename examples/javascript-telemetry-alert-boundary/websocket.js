const WebSocket = require("ws");
const config = require("./config");
const { checkPolygonBoundaries } = require("./geojson");

/**
 * Connect to the Skydio telemetry WebSocket and handle messages
 * @param {string} vehicleSerial - Vehicle serial number
 * @param {string} wsUrl - WebSocket URL with authentication
 * @param {boolean} debug - Whether to enable debug logging
 * @returns {WebSocket} The WebSocket instance
 */
function connectToTelemetryWs(vehicleSerial, wsUrl, debug = false) {
  console.log(`   Connecting to telemetry stream...`);

  const ws = new WebSocket(wsUrl);

  ws.on("open", () => {
    console.log(`   ✓ Connected, listening for telemetry...`);
  });

  ws.on("message", (message) => {
    try {
      const data = JSON.parse(message);
      
      if (debug) {
        console.log(`[DEBUG] Raw telemetry data:`, JSON.stringify(data, null, 2));
      }
      
      // Extract position data if available
      // The telemetry data has lat/lon directly on the root object
      if (data.lat != null && data.lon != null) {
        const lat = data.lat;
        const lng = data.lon;
        
        if (debug) {
          console.log(`[DEBUG] Position detected: lat=${lat}, lng=${lng}`);
        }
        
        checkPolygonBoundaries(lat, lng, vehicleSerial);
      } else if (debug) {
        console.log(`[DEBUG] No position data in this message. Available keys:`, Object.keys(data));
      }
      
      // Optional: Log full telemetry data (uncomment to see all data)
      // console.log(`[${vehicleSerial}] Telemetry:`, JSON.stringify(data, null, 2));
    } catch (error) {
      console.error(`Error parsing message for ${vehicleSerial}:`, error.message);
      if (debug) {
        console.error(`[DEBUG] Raw message that failed to parse:`, message.toString());
      }
    }
  });

  ws.on("error", (error) => {
    console.error(`\n✗ WebSocket error for ${vehicleSerial}:`, error.message);
    
    if (error.message.includes("401")) {
      console.error("\n❌ AUTHENTICATION ERROR (401 Unauthorized)");
      console.error("   Possible causes:");
      console.error("   1. API token is invalid or expired");
      console.error("   2. API token doesn't have permission to access this vehicle");
      console.error("   3. Token format is incorrect (should be the token value only, no 'ApiToken' prefix)");
      console.error("   4. Vehicle serial number is incorrect");
      console.error("\n   How to fix:");
      console.error("   - Check your API token in Skydio Cloud: Settings -> API Tokens");
      console.error("   - Verify the token has 'vehicle:read' or 'vehicle:*' scope");
      console.error("   - Verify vehicle serial: Settings -> Devices -> Your Vehicle");
      console.error("   - Make sure to export just the token value:");
      console.error("     export API_TOKEN_SECRET=abc123xyz...");
      console.error();
    }
    
    if (debug) {
      console.error(`[DEBUG] Full error object:`, error);
    }
  });

  ws.on("close", (code, reason) => {
    const details = [
      reason && reason.length > 0 ? `reason=${reason}` : null,
      code === 1008 ? "(policy violation - usually auth failure)" : null,
    ].filter(Boolean).join(" ");
    
    console.log(`   ✗ Disconnected (code=${code})${details ? " " + details : ""}`);
  });

  return ws;
}

module.exports = {
  connectToTelemetryWs,
};
