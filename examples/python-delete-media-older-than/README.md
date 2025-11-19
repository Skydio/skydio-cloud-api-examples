# Skydio API Example: Python Delete Media Older Than

This script demonstrates how to use the Skydio Cloud API to delete media files older than a specified time period. It's useful for helping customers manage their cloud storage by removing old media files.

## Features

- **Dry Run Mode**: Default mode that lists what would be deleted without actually deleting
- **Flexible Time Periods**: Supports formats like `14d`, `30d`, `2w`, `3m`
- **Pagination Support**: Automatically handles large datasets
- **Progress Tracking**: Shows detailed progress during deletion
- **Human-Readable Output**: Displays file counts and sizes

## API Endpoints Used

- `GET /v0/media_files` - List media files with filtering
- `DELETE /v0/media/{uuid}/delete` - Delete a specific media file

## Prerequisites

You need a Skydio API Token and API Token ID, which can be obtained from:
1. Go to https://cloud.skydio.com
2. Navigate to Settings → Integrations
3. Create or view an API Token
4. Click "Details" to see the API Token ID

## Setup

Follow the instructions in the [README.md](../../README.md) file in the root directory of this repository to set up your environment.

Then set your API credentials as environment variables:

**Unix/Mac:**
```bash
export API_TOKEN="your_skydio_api_token"
export API_TOKEN_ID="your_skydio_api_token_id"
```

**Windows PowerShell:**
```powershell
$env:API_TOKEN = "your_skydio_api_token"
$env:API_TOKEN_ID = "your_skydio_api_token_id"
```

## Usage

### Dry Run (Default)

See what would be deleted without actually deleting:

```bash
python main.py --before 14d
```

This will:
1. Fetch all media files captured more than 14 days ago
2. Display a sample of files that would be deleted
3. Show total count and size
4. Exit without deleting anything

### Actually Delete Files

To perform the actual deletion, add the `--delete` flag:

```bash
python main.py --before 30d --delete
```

⚠️ **Warning**: This will permanently delete files from Skydio Cloud. This action cannot be undone!

### Time Period Formats

The `--before` argument accepts various formats:

**Relative time periods:**
- `14d` or `"14 days"` - Delete files older than 14 days
- `2w` or `"2 weeks"` - Delete files older than 2 weeks (14 days)
- `3m` or `"3 months"` - Delete files older than 3 months (~90 days)
- `5min` or `"5 minutes"` - Delete files older than 5 minutes
- `2hr` or `"2 hours"` - Delete files older than 2 hours

**Absolute dates (uses 00:00:00 in your local timezone):**
- `2024-01-15` - Delete files captured before January 15, 2024 at midnight (local time)
- `2024/01/15` - Same as above with different separator
- `01-15-2024` - MM-DD-YYYY format
- `01/15/2024` - MM/DD/YYYY format

### Examples

```bash
# Dry run: See what would be deleted (14 days)
python main.py --before 14d

# Dry run: See what would be deleted (30 days)
python main.py --before 30d

# Actually delete media older than 30 days
python main.py --before 30d --delete

# Delete media older than 2 weeks
python main.py --before 2w --delete

# Delete media older than 3 months
python main.py --before 3m --delete

# Delete media captured before a specific date (midnight local time)
python main.py --before 2024-01-15 --delete

# Delete media captured in the last 5 minutes (useful for testing)
python main.py --before 5min --delete
```

### Using a Different API Environment

By default, the script uses `https://api.skydio.com/api/v0`. To use a different environment, set
the BASE_URL environment variable:

```bash
export BASE_URL="https://api.your.skydio.server/api/v0"
python main.py --before 14d
```

## How It Works

1. **Authentication**: Uses `API_TOKEN` and `API_TOKEN_ID` from environment variables
2. **Query**: Calls `GET /v0/media_files` with `captured_before`, `per_page`, and `page_number` parameters
3. **Pagination**: Automatically fetches all pages of results (up to 500 files per page)
4. **Dry Run Display**: Shows sample files and total statistics
5. **Deletion**: If `--delete` is passed, calls `DELETE /v0/media/{uuid}/delete` for each file
6. **Progress**: Shows real-time progress and success/failure for each file

## Sample Output

### Dry Run Mode
```
======================================================================
Delete Old Media Files
======================================================================
API Base URL: https://api.skydio.com/api/v0
Cutoff date: 2024-10-30T17:00:00Z (14d ago)
Mode: DRY RUN
======================================================================

⚠ DRY RUN MODE: No data will be deleted. Use --delete to actually delete.

Fetching media files captured before 2024-10-30T17:00:00Z...
  Page 1: Found 100 files (total so far: 100)
  Page 2: Found 45 files (total so far: 145)
Total media files found: 145

DRY RUN: Would delete 145 media files
Total size: 2.34 GB
Captured before: 2024-10-30T17:00:00Z

Sample of files that would be deleted:
  - abc123-uuid: PHOTO (12.45 MB) captured at 2024-10-25T14:30:00Z
  - def456-uuid: VIDEO (145.67 MB) captured at 2024-10-24T10:15:00Z
  ... and 143 more files

To actually delete these files, re-run with --delete flag

======================================================================
Summary
======================================================================
DRY RUN completed. Use --delete flag to actually delete media.
======================================================================
```

### Delete Mode
```
======================================================================
Delete Old Media Files
======================================================================
API Base URL: https://api.skydio.com/api/v0
Cutoff date: 2024-10-30T17:00:00Z (14d ago)
Mode: DELETE
======================================================================

Fetching media files captured before 2024-10-30T17:00:00Z...
  Page 1: Found 100 files (total so far: 100)
  Page 2: Found 45 files (total so far: 145)
Total media files found: 145

Deleting 145 media files
Total size: 2.34 GB
Captured before: 2024-10-30T17:00:00Z

Deleting files...
  [1/145] ✓ Deleted abc123-uuid
  [2/145] ✓ Deleted def456-uuid
  ...
  [145/145] ✓ Deleted xyz789-uuid

======================================================================
Summary
======================================================================
Total deleted: 145
Total failed: 0
======================================================================
```

## Safety Features

- **Dry Run Default**: Script defaults to dry-run mode to prevent accidental deletions
- **Explicit Delete Flag**: Requires `--delete` flag for actual deletion
- **Error Handling**: Catches and reports errors without stopping the entire process
- **Progress Tracking**: Shows which files succeeded and which failed
- **Summary Report**: Provides detailed summary at the end

## Troubleshooting

### Missing Environment Variables
```
Error: API_TOKEN environment variable is not set.
```
**Solution**: Make sure to export both `API_TOKEN` and `API_TOKEN_ID` before running the script.

### Invalid Time Format
```
Error: Invalid time format: '14'. Expected format like '14d', '2w', or '3m'
```
**Solution**: Use a valid time format like `14d`, `2w`, or `3m`.

### HTTP Errors
If you encounter HTTP errors, check:
- Your API token is valid and not expired
- Your API token has the `WRITE_MEDIA` scope enabled
- The API base URL is correct for your environment

## API Token Scopes Required

This script requires an API token with the following scopes:
- `READ_MEDIA` - To list media files
- `WRITE_MEDIA` - To delete media files

## For More Information

- [Skydio Cloud API Reference](https://apidocs.skydio.com/)
- [Media Endpoints Documentation](https://apidocs.skydio.com/reference/get_v0-media-files)
