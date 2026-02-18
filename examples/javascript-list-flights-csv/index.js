const axios = require("axios");
const fs = require("fs");

const API_TOKEN_SECRET = process.env.API_TOKEN_SECRET || "";
const BASE_URL = "https://api.skydio.com/api/v0";
const PER_PAGE = 50;

const CSV_COLUMNS = [
  "flight_id",
  "incident_id",
  "pilot_email",
  "takeoff_time",
  "landing_time",
  "takeoff_latitude",
  "takeoff_longitude",
  "duration",
  "sensor_package",
  "attachments",
];

function getHeaders() {
  return {
    Accept: "application/json",
    Authorization: API_TOKEN_SECRET,
  };
}

function getDeep(obj, ...path) {
  let cur = obj;
  for (const key of path) {
    if (cur == null) return "";
    if (typeof key === "number") {
      if (!Array.isArray(cur) || key >= cur.length) return "";
      cur = cur[key];
    } else {
      cur = typeof cur === "object" ? cur[key] : undefined;
    }
  }
  return cur ?? "";
}

function roundToSecond(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString);
  if (isNaN(d.getTime())) return "";
  d.setMilliseconds(0);
  return d.toISOString();
}

function computeDuration(takeoff, landing) {
  if (!takeoff || !landing) return "";
  const ms = new Date(landing).getTime() - new Date(takeoff).getTime();
  return isNaN(ms) ? "" : (ms / 1000).toFixed(0);
}

function buildAttachments(flight) {
  const atts = flight.attachments;
  if (!Array.isArray(atts) || atts.length === 0) return "";
  return atts
    .map((a) => a?.attachment_type)
    .filter(Boolean)
    .join("+");
}

function buildRow(flight) {
  return {
    flight_id: flight.flight_id ?? "",
    incident_id: flight.incident_id ?? "",
    pilot_email: flight.user_email ?? "",
    takeoff_time: roundToSecond(flight.takeoff),
    takeoff_latitude: flight.takeoff_latitude ?? "",
    takeoff_longitude: flight.takeoff_longitude ?? "",
    landing_time: roundToSecond(flight.landing),
    duration: computeDuration(flight.takeoff, flight.landing),
    sensor_package: getDeep(flight, "sensor_package", "sensor_package_type"),
    attachments: buildAttachments(flight),
  };
}

function escapeCsvField(value) {
  const str = String(value);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function rowToCsvLine(row) {
  return CSV_COLUMNS.map((col) => escapeCsvField(row[col])).join(",");
}

async function fetchFlightPage(pageNumber, since) {
  const params = { per_page: PER_PAGE, page_number: pageNumber };
  if (since) params.since = since;

  const response = await axios.get(`${BASE_URL}/flights`, {
    headers: getHeaders(),
    params,
  });

  const body = response.data;
  const data = body.data ?? body;
  const flights = data.flights ?? [];
  const pagination = data.pagination ?? {};

  return { flights, pagination };
}

async function main() {
  const sinceArg = process.argv[2];
  if (sinceArg && isNaN(Date.parse(sinceArg))) {
    console.error(`Invalid ISO date: ${sinceArg}`);
    console.error("Usage: node index.js [ISO_DATE]");
    console.error("Example: node index.js 2025-01-01T00:00:00Z");
    process.exit(1);
  }

  if (!API_TOKEN_SECRET) {
    console.error("Error: API_TOKEN_SECRET environment variable is not set.");
    process.exit(1);
  }

  const outputFile = "flights.csv";
  const writeStream = fs.createWriteStream(outputFile);
  writeStream.write(CSV_COLUMNS.join(",") + "\n");

  let pageNumber = 1;
  let totalPages = null;
  let totalExported = 0;

  while (true) {
    console.error(`Fetching page ${pageNumber}${totalPages != null ? ` / ${totalPages}` : ""}...`);

    const { flights, pagination } = await fetchFlightPage(pageNumber, sinceArg);

    if (pageNumber === 1 && pagination.total_pages != null) {
      totalPages = pagination.total_pages;
      console.error(`Total pages: ${totalPages}`);
    }

    if (flights.length === 0) break;

    for (const flight of flights) {
      const row = buildRow(flight);
      writeStream.write(rowToCsvLine(row) + "\n");
      totalExported++;
    }

    if (totalPages != null && pageNumber >= totalPages) break;
    if (totalPages == null && flights.length < PER_PAGE) break;

    pageNumber++;
  }

  writeStream.end();
  await new Promise((resolve) => writeStream.on("finish", resolve));

  console.error(`\nSuccessfully exported ${totalExported} flights to ${outputFile}`);
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
