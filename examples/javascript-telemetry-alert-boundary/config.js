// ----------------- CONFIGURATION ------------------
// Get configuration from environment variables

module.exports = {
  API_TOKEN_SECRET: process.env.API_TOKEN_SECRET,
  GEOJSON_FILE: process.env.GEOJSON_FILE || process.argv[2],
  DEBUG: process.env.DEBUG === "true" || process.env.DEBUG === "1",
  POLL_INTERVAL_MS: parseInt(process.env.POLL_INTERVAL_MS || "60000", 10), // Default 1 minute
};
