const axios = require("axios");
const config = require("./config");

const BASE_URL = "https://api.skydio.com/api/v0";

/**
 * Get headers for API requests
 * @returns {Object} Headers with authorization
 */
function getHeaders() {
  return {
    Accept: "application/json",
    Authorization: `ApiToken ${config.API_TOKEN_SECRET}`,
  };
}

/**
 * Fetch all vehicles from the Skydio Cloud API
 * @returns {Promise<Array>} Array of vehicle objects
 */
async function getVehicles() {
  try {
    const url = `${BASE_URL}/vehicles`;
    const response = await axios.get(url, { headers: getHeaders() });
    const vehicles = response.data?.data?.vehicles || [];

    if (config.DEBUG) {
      console.log(`[DEBUG] Found ${vehicles.length} vehicle(s):`);
      vehicles.forEach((v) => {
        console.log(`  - ${v.vehicle_serial} (${v.name || "unnamed"}): flight_status=${v.flight_status}, is_online=${v.is_online}`);
      });
    }

    return vehicles;
  } catch (error) {
    console.error("Error fetching vehicles:", error.message);
    if (error.response) {
      console.error(`  Status: ${error.response.status}`);
      console.error(`  Data:`, JSON.stringify(error.response.data, null, 2));
    }
    return [];
  }
}

const ACTIVE_FLIGHT_STATUSES = ["PREP", "FLYING"];

/**
 * Filter vehicles that are in PREP or FLYING flight_status
 * @param {Array} vehicles - Array of vehicle objects
 * @returns {Array} Filtered array of active vehicles
 */
function getActiveVehicles(vehicles) {
  return vehicles.filter((vehicle) =>
    ACTIVE_FLIGHT_STATUSES.includes(vehicle.flight_status)
  );
}

module.exports = {
  getVehicles,
  getActiveVehicles,
};
