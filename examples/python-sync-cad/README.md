# Python CAD Sync Example

This example demonstrates how to sync Computer-Aided Dispatch (CAD) events from a local database to the Skydio Markers API. It consists of three main components:

1.  **Database**: A simple SQLite database to store CAD events.
2.  **Event Generator**: A script that simulates new CAD events and adds them to the database every 5 seconds.
3.  **Sync Service**: A service that reads new events from the database and creates corresponding markers in Skydio Cloud.

See it in action:

https://www.loom.com/share/e2b1f0917bb84e9da632e38aaf68c748

## Setup

1.  **Install Dependencies**: Navigate to this directory and install the required Python packages.

    ```bash
    pip install -e .
    ```

2.  **Initialize the Database**: Run the database script to create the `cad_events.db` file and the necessary tables.

    ```bash
    python3 database.py
    ```

3.  **Configure Environment Variables**: Create a `.env` file by copying the example file. Then, edit it to add your Skydio API key.

    ```bash
    cp .env.example .env
    # Now edit the .env file with your credentials
    ```

## Running the Services

You will need to run the event generator and the sync service in two separate terminal windows.

**Terminal 1: Start the Event Generator**

This script will start adding new CAD events to the database, simulating an actual CAD system.

```bash
python3 event_generator.py
```

**Terminal 2: Start the Sync Service**

This service will connect to the database, find unsynced events, and create markers for them in Skydio Cloud.

```bash
python3 sync_service.py
```

You should now see events being created in the first terminal and synced to Skydio in the second terminal.

This example demonstrates how to sync Computer-Aided Dispatch (CAD) events from a local database to the Skydio Markers API. It consists of three main components:

1.  **Database**: A simple SQLite database to store CAD events.
2.  **Event Generator**: A script that simulates new CAD events and adds them to the database every 5 seconds.
3.  **Sync Service**: A service that reads new events from the database and creates corresponding markers in Skydio Cloud.
