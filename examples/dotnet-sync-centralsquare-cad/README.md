## .NET CentralSquare CAD to Skydio Cloud Marker Sync Example

> ⚠️ **CentralSquare integration is available directly through Axon Fusus, so this example is not needed to integrate CentralSquare with Skydio Cloud if you use Fusus.**

> 🙏 **We are grateful to the Pasco Sheriff's Office (https://www.pascosheriff.com/) for generously contributing this example. If you have questions about using or adapting this integration, please contact Skydio Support through your usual Skydio channels.**

This example demonstrates how to synchronize active CAD (Computer Aided Dispatch) incidents
from a CentralSquare CAD SQL Server database into **Skydio Cloud markers** using a .NET console application.

The app:

- **Reads active incidents** from a CAD `incident` table via Entity Framework Core.
- **Fetches existing markers** from the Skydio Cloud Markers API.
- **Deletes markers** for incidents that are no longer active.
- **Creates or updates markers** for currently active incidents.

Use this as a starting point to integrate your CentralSquare CAD system with Skydio Cloud.

## Project layout

- `Skydio.sln` – .NET solution file.
- `SkydioInterfaceConsoleApp/` – .NET 8 console app that performs the sync.
  - `Program.cs` – main sync logic.
  - `appsettings.json` – database connection string, Skydio API key, logging.
  - `DB/CAD_Manual/Incident.cs` – EF Core model for the CAD `incident` table.
  - `DB/CAD_Manual/CadContext_Manual.cs` – EF Core `DbContext` for CAD.
  - `SkydioRequestBo.cs` – request bodies for create/update marker calls.
  - `ResponseBo/*.cs` – response DTOs for Skydio marker API.

Target framework: **.NET 8.0** (`net8.0`).

## Prerequisites

- **.NET SDK 8.0 or later** installed.
  - macOS example:
    ```bash
    brew install dotnet-sdk
    ```
- **CentralSquare CAD database (SQL Server)** reachable from where you run this app.
- **Skydio Cloud API key** with permission to read and manage markers.

## Configuration (`appsettings.json`)

All configuration lives in `SkydioInterfaceConsoleApp/appsettings.json`.

### CAD database connection

```json
"ConnectionStrings": {
  "CADRPT": "Data Source=CAD_SERVER_NAME;initial catalog=cad;persist security info=True;user id=CAD_USER_NAME;password=CAD_DATABASE_PASSWORD;TrustServerCertificate=True;"
}
```

Update `CADRPT` to point at your CentralSquare CAD database (server, database name, credentials).

`CadContext_Manual.cs` uses this connection string to connect to SQL Server, and
`Incident.cs` maps to the `incident` table (incident id, lat/lon, nature, etc.).

### Skydio Cloud API key

```json
"Secrets": {
  "AuthorizationAPIKey": "INSERT_KEY_FROM_SKYDIO_API"
}
```

Replace `INSERT_KEY_FROM_SKYDIO_API` with your Skydio Cloud API key.
The app sends this value as the `Authorization` header on all Skydio API calls.

### Logging

The `Serilog` section in `appsettings.json` configures file and console logging.
By default it writes rolling log files under `logs/webapi-.log` and logs to console.

## How the sync works (high level)

1. **Load configuration and logging**
   - Reads `appsettings.json` and configures Serilog.
2. **Query CAD incidents**
   - Uses `CadContext` to read from `Incident`.
   - Filters to incidents with non-empty, non-zero latitude and longitude.
3. **Fetch Skydio markers**
   - Calls `GET /api/v0/markers` (last 12 months) and deserializes into
     `SkydioGetMarkersResponseBo`.
4. **Delete markers no longer active**
   - Looks at markers where `source_name` starts with `"OS CAD"`.
   - If a marker’s `marker_details.incident_id` no longer appears in the active
     CAD incidents, the app calls `DELETE /api/v0/marker/{uuid}/delete`.
   - Deletes are limited to **25 per run**.
5. **Create or update markers for active incidents**
   - For each active incident:
     - If no existing marker with matching incident id is found, builds a
       `SkydioCreateMarkerRequestBo` and `POST`s to `/api/v0/marker`.
     - If a marker already exists and key fields (lat/lon, nature code, or
       event time minute) have changed, builds a `SkydioUpdateMarkerRequestBo`
       and `POST`s to `/api/v0/marker` to update it.

Markers created by this integration use:

- `source_name = "OS CAD"`
- `type = "INCIDENT"`
- `marker_details` to carry CAD-specific metadata such as incident id,
  priority, and nature code.

## Running the example

From the `dotnet-sync-centralsquare-cad` folder (where `Skydio.sln` is located):

```bash
# Optional: restore NuGet packages explicitly
dotnet restore

# Run the console app
dotnet run --project SkydioInterfaceConsoleApp/SkydioInterfaceConsoleApp.csproj
```

Or, from inside the project folder:

```bash
cd ./SkydioInterfaceConsoleApp
dotnet run
```

When you run it, the app will:

- Log startup and configuration info.
- Query active CAD incidents.
- Reconcile Skydio markers (delete, create, update) with the current incidents.
- Log each marker creation/update/delete and a summary when processing completes.

You can schedule this console app to run periodically (for example via cron or
a job scheduler) to keep Skydio Cloud markers in sync with your CAD system.
