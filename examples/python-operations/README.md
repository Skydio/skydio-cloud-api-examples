# Skydio API Example: Operations

These scripts demonstrate how to use the Skydio Cloud Operations API to read operations,
their event timelines, and their operation reports (including DFR outcomes).

> The Operations API is in early access. Contact Skydio to have it enabled for your organization.

| Script | What it does |
|--------|--------------|
| `list_operations.py` | Lists operations, filtered by state and start/end time, and optionally saves them to CSV |
| `get_operation.py` | Prints one operation's details, event timeline, and the questions and answers in its submitted reports |
| `dfr_outcomes_dashboard/main.py` | Exports DFR outcomes and on-scene response times to CSV and a self-contained HTML dashboard. See [its README](dfr_outcomes_dashboard/README.md) |
| `skydio_operations.py` | Helpers shared by the scripts: pagination and one function per endpoint |
| `skydio_api_client.py` | The `SkydioAPIClient` from the `python-marker-crud` example |

## API token scopes

Create an API token in Skydio Cloud under Integrations, with these scopes:

- **Operations**, for `GET /v0/operations` and `GET /v0/operation/<id>`
- **Operation Reports**, for `GET /v0/operation_reports` and `GET /v0/operation_report/<id>`

Only submitted reports are returned. Drafts are not.

## Usage

Follow the instructions in the [README.md](../../README.md) file in the root directory of this
repository. `pip install -e .` installs the dependencies and makes the shared helpers importable
from the `dfr_outcomes_dashboard` subfolder.

Then run the scripts from this folder:

```bash
# Closed operations that started since October 1, saved to CSV
python list_operations.py --state CLOSED --start-since 2026-10-01 --csv operations.csv

# One operation with its timeline and reports
python get_operation.py <operation_id>

# DFR outcomes CSV + HTML dashboard for the last 30 days
python dfr_outcomes_dashboard/main.py
```

Dates and times are ISO 8601, for example `2026-10-01` or `2026-10-01T08:00:00-07:00`. Values
without a time zone are treated as UTC.

The scripts call `https://api.skydio.com/api` by default. To use a different server, such as an
on-prem deployment, set `SKYDIO_API_URL`, for example
`export SKYDIO_API_URL="https://skydio.example.org/api"`.
