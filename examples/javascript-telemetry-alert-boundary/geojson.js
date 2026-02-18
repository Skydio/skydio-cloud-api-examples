const fs = require("fs");
const path = require("path");
const booleanPointInPolygon = require("@turf/boolean-point-in-polygon").default;
const { point } = require("@turf/helpers");

// Track which polygons the drone is currently inside
const droneInPolygons = new Set();
let polygons = [];

/**
 * Load and parse GeoJSON file containing polygon boundaries
 * @param {string} filePath - Path to the GeoJSON file
 * @returns {Array} Array of polygon objects with id, name, geometry, and properties
 */
function loadGeoJSON(filePath) {
  try {
    const fullPath = path.resolve(filePath);
    const data = fs.readFileSync(fullPath, "utf8");
    const geojson = JSON.parse(data);
    
    console.log(`\n🗺️  Loading GeoJSON file: ${filePath}`);
    
    const features = geojson.type === "FeatureCollection" 
      ? geojson.features 
      : [geojson];
    
    polygons = features
      .filter(feature => 
        feature.geometry.type === "Polygon" || 
        feature.geometry.type === "MultiPolygon"
      )
      .map((feature, index) => ({
        id: feature.properties?.id || feature.properties?.name || `polygon-${index}`,
        name: feature.properties?.name || `Polygon ${index + 1}`,
        geometry: feature.geometry,
        properties: feature.properties || {}
      }));
    
    console.log(`   Found ${polygons.length} polygon(s)`);
    polygons.forEach(p => console.log(`   - ${p.name} (${p.id})`));
    
    return polygons;
  } catch (error) {
    console.error(`✗ Error loading GeoJSON file: ${error.message}`);
    process.exit(1);
  }
}

/**
 * Check if the drone's current position is inside any of the loaded polygons
 * and log entry/exit events
 * @param {number} latitude - Drone's current latitude
 * @param {number} longitude - Drone's current longitude
 * @param {string} vehicleSerial - Vehicle serial number for logging
 */
function checkPolygonBoundaries(latitude, longitude, vehicleSerial) {
  const pt = point([longitude, latitude]);
  
  polygons.forEach(polygon => {
    const isInside = booleanPointInPolygon(pt, polygon.geometry);
    const wasInside = droneInPolygons.has(polygon.id);
    
    if (isInside && !wasInside) {
      droneInPolygons.add(polygon.id);
      console.log(`\n🟢 [${vehicleSerial}] ENTERED "${polygon.name}"`);
      console.log(`   Location: [${latitude.toFixed(6)}, ${longitude.toFixed(6)}]`);
      console.log(`   Polygon:  ${polygon.id}`);
      if (polygon.properties.severity) {
        console.log(`   Severity: ${polygon.properties.severity}`);
      }
    } else if (!isInside && wasInside) {
      droneInPolygons.delete(polygon.id);
      console.log(`\n🔴 [${vehicleSerial}] LEFT "${polygon.name}"`);
      console.log(`   Location: [${latitude.toFixed(6)}, ${longitude.toFixed(6)}]`);
      console.log(`   Polygon:  ${polygon.id}`);
      if (polygon.properties.severity) {
        console.log(`   Severity: ${polygon.properties.severity}`);
      }
    }
  });
}

module.exports = {
  loadGeoJSON,
  checkPolygonBoundaries,
};
