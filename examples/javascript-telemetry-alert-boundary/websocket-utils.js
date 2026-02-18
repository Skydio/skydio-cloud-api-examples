const config = require("./config");

/**
 * Build the websocket URL with the API token and vehicle serial.
 * NOTE: When troubleshooting, make sure that this URL is correct by comparing it to the one in the
 * Skydio Cloud UI, under Settings -> Devices -> Your vehicle -> Connectivity -> Streaming.
 * @param {string} vehicleSerial - Vehicle serial number
 * @returns {string} WebSocket URL with authentication token
 */
function buildWsUrl(vehicleSerial) {
  if (config.DEBUG) {
    console.log("\n=== DEBUG INFO ===");
    console.log(`Vehicle Serial: ${vehicleSerial}`);
    console.log(`API_TOKEN_SECRET is set: ${!!config.API_TOKEN_SECRET}`);
    
    if (config.API_TOKEN_SECRET) {
      console.log(`API_TOKEN_SECRET length: ${config.API_TOKEN_SECRET.length} characters`);
      console.log(`API_TOKEN_SECRET starts with: ${config.API_TOKEN_SECRET.substring(0, 10)}...`);
      console.log(`API_TOKEN_SECRET ends with: ...${config.API_TOKEN_SECRET.substring(config.API_TOKEN_SECRET.length - 10)}`);
    }
    console.log("===================\n");
  }
  
  if (!config.API_TOKEN_SECRET) {
    console.log("⚠️  WARNING: API_TOKEN_SECRET is not set. Connection will likely fail.");
    const basicUrl = `wss://stream.skydio.com/data/${vehicleSerial}`;
    return basicUrl;
  }
  
  const url = `wss://stream.skydio.com/data/${vehicleSerial}?token=${config.API_TOKEN_SECRET}`;
  
  if (config.DEBUG) {
    console.log(`WebSocket URL format: wss://stream.skydio.com/data/${vehicleSerial}?token=***`);
    console.log(`Full URL: ${url}\n`);
  }
  
  return url;
}

module.exports = {
  buildWsUrl,
};
