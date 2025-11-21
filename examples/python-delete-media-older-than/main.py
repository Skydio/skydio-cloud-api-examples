import os
import argparse
import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

# ----------------- CONFIGURATION ------------------
# Get API token from environment variables
API_TOKEN = os.getenv("API_TOKEN")  # Must be set before running the script
API_TOKEN_ID = os.getenv("API_TOKEN_ID")  # Must be set before running the script
BASE_URL = os.getenv("BASE_URL", "https://api.skydio.com/api/v0")


# ----------------- HELPER FUNCTIONS ------------------
def get_headers() -> dict:
    """Get headers for API requests."""
    if not API_TOKEN:
        raise EnvironmentError("API_TOKEN environment variable is not set.")
    if not API_TOKEN_ID:
        raise EnvironmentError("API_TOKEN_ID environment variable is not set.")
    return {
        "Accept": "application/json",
        "Authorization": f"ApiToken {API_TOKEN}",
        "X-Api-Token-Id": API_TOKEN_ID,
    }


def parse_time_delta(time_str: str) -> Optional[timedelta]:
    """
    Parse a time delta string like '14d', '30d', '7d' into a timedelta.

    Supported formats:
    - '14d' or '14 days' -> 14 days
    - '2w' or '2 weeks' -> 14 days
    - '3m' or '3 months' -> ~90 days (30 days per month)
    - '5min' or '5 minutes' -> 5 minutes
    - '2hr' or '2 hours' -> 2 hours

    Args:
        time_str: String representation of time delta

    Returns:
        timedelta object, or None if the string is not a time delta format

    Raises:
        ValueError: If the format is invalid
    """
    time_str = time_str.strip().lower()

    # Match patterns like "14d", "14 days", "2w", "2 weeks", "3m", "3 months"
    match = re.match(r"^(\d+)\s*(d|day|days|w|week|weeks|m|month|months|sec|seconds|min|minutes|hr|hours)$", time_str)
    if not match:
        return None  # Not a time delta format

    value = int(match.group(1))
    unit = match.group(2)

    if unit in ("sec", "seconds"):
        return timedelta(seconds=value)
    elif unit in ("min", "minutes"):
        return timedelta(minutes=value)
    elif unit in ("hr", "hours"):
        return timedelta(hours=value)
    elif unit in ("d", "day", "days"):
        return timedelta(days=value)
    elif unit in ("w", "week", "weeks"):
        return timedelta(weeks=value)
    elif unit in ("m", "month", "months"):
        # Approximate months as 30 days
        return timedelta(days=value * 30)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")


def get_cutoff_datetime(before_str: str) -> datetime:
    """
    Calculate the cutoff datetime based on the --before argument.

    Args:
        before_str: String like '14d' meaning 14 days ago, or a date like '2024-01-15'

    Returns:
        datetime object representing the cutoff time (in UTC)

    Raises:
        ValueError: If the format is invalid
    """
    # Try to parse as a time delta first (e.g., "14d", "2w", "3m")
    delta = parse_time_delta(before_str)
    if delta is not None:
        cutoff = datetime.utcnow() - delta
        return cutoff

    # Try to parse as a date (e.g., "2024-01-15", "2024/01/15")
    # This will use 00:00:00 in the user's local timezone
    date_formats = [
        "%Y-%m-%d",      # 2024-01-15
        "%Y/%m/%d",      # 2024/01/15
        "%m-%d-%Y",      # 01-15-2024
        "%m/%d/%Y",      # 01/15/2024
    ]

    for date_format in date_formats:
        try:
            # Parse the date (assumes 00:00:00 local time)
            local_dt = datetime.strptime(before_str.strip(), date_format)
            # Since strptime creates a naive datetime, calling .timestamp() interprets it
            # as local time and converts to UTC timestamp. Then we create a UTC datetime.
            # This is equivalent to: local midnight -> UTC
            return datetime.utcfromtimestamp(local_dt.timestamp())
        except ValueError:
            continue

    # If nothing worked, raise an error
    raise ValueError(
        f"Invalid format: '{before_str}'. "
        "Expected a time delta like '14d', '2w', '3m', or a date like '2024-01-15'"
    )


def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_all_old_media_files(cutoff_datetime: datetime) -> List[Dict[str, Any]]:
    """
    Fetch all media files older than the cutoff datetime using pagination.

    Args:
        cutoff_datetime: Only fetch files captured before this time

    Returns:
        List of media file dictionaries
    """
    all_files = []
    page_number = 1

    cutoff_iso = cutoff_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Fetching media files captured before {cutoff_iso}...")

    while True:
        url = f"{BASE_URL}/media_files"
        params = {
            "captured_before": cutoff_iso,
            "per_page": 500,  # Max allowed per page
            "page_number": page_number,
        }

        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()

        data = response.json().get("data", {})
        files = data.get("files", [])
        pagination = data.get("pagination", {})

        all_files.extend(files)

        print(f"  Page {page_number}: Found {len(files)} files (total so far: {len(all_files)})")

        # Check if there are more pages
        current_page = pagination.get("current_page", page_number)
        total_pages = pagination.get("total_pages", 1)

        if current_page >= total_pages:
            break

        page_number += 1

    print(f"Total media files found: {len(all_files)}")

    return all_files


def delete_media_file(file_uuid: str) -> Tuple[bool, str]:
    """
    Delete a single media file by UUID.

    Args:
        file_uuid: UUID of the file to delete

    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    url = f"{BASE_URL}/media/{file_uuid}/delete"
    try:
        response = requests.delete(url, headers=get_headers())
        response.raise_for_status()
        return True, None
    except requests.exceptions.HTTPError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def delete_old_media_files(
    cutoff_datetime: datetime,
    dry_run: bool = True,
) -> Tuple[int, int]:
    """
    Delete media files older than the cutoff datetime.

    Args:
        cutoff_datetime: Delete files captured before this time
        dry_run: If True, only list files without deleting

    Returns:
        Tuple of (deleted_count, failed_count)
    """
    files = get_all_old_media_files(cutoff_datetime)

    if not files:
        print("No media files found to delete.")
        return 0, 0

    # Calculate total size
    total_size = sum(f.get("size", 0) for f in files)

    print(f"\n{'DRY RUN: Would delete' if dry_run else 'Deleting'} {len(files)} media files")
    print(f"Total size: {format_size(total_size)}")
    print(f"Captured before: {cutoff_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}\n")

    if dry_run:
        print(f"{len(files)} files that would be deleted:")
        for file in files:
            captured_time = file.get("captured_time", "unknown")
            print(f"  - {file['uuid']}: {file.get('kind', 'unknown')} "
                  f"({format_size(file.get('size', 0))}) "
                  f"captured at {captured_time}")

        print(f"\nTo actually delete these files, re-run with --delete flag")
        return 0, 0

    # Delete files one by one
    deleted_count = 0
    failed_count = 0

    print("Deleting files...")
    for i, file in enumerate(files, 1):
        file_uuid = file["uuid"]

        success, error = delete_media_file(file_uuid)

        if success:
            print(f"  [{i}/{len(files)}] ✓ Deleted {file_uuid}")
            deleted_count += 1
        else:
            print(f"  [{i}/{len(files)}] ✗ Failed to delete {file_uuid}: {error}")
            failed_count += 1

    return deleted_count, failed_count


# ----------------- MAIN SCRIPT ------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete media files from Skydio Cloud older than a specified time period",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default) - see what would be deleted
  python main.py --before 14d

  # Actually delete media older than 30 days
  python main.py --before 30d --delete

  # Delete media older than 2 weeks
  python main.py --before 2w --delete

  # Delete media captured before a specific date (uses local timezone at 00:00:00)
  python main.py --before 2024-01-15 --delete

Time formats:
  14d or 14 days    - 14 days ago
  2w or 2 weeks     - 2 weeks ago
  3m or 3 months    - 3 months ago (~90 days)
  5min or 5 minutes - 5 minutes ago
  2hr or 2 hours    - 2 hours ago

Date formats (uses 00:00:00 in your local timezone):
  2024-01-15        - YYYY-MM-DD
  2024/01/15        - YYYY/MM/DD
  01-15-2024        - MM-DD-YYYY
  01/15/2024        - MM/DD/YYYY

Environment variables required:
  API_TOKEN       - Your Skydio API token
  API_TOKEN_ID    - Your Skydio API token ID
  BASE_URL        - (Optional) API base URL (default: https://api.skydio.com/api/v0)
        """
    )
    parser.add_argument(
        "--before",
        type=str,
        required=True,
        help="Delete media older than this time period (e.g., '14d', '30d', '2w', '3m') or before a specific date (e.g., '2024-01-15')",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete the media (default is dry-run mode)",
    )
    args = parser.parse_args()

    # Parse the time delta
    try:
        cutoff_datetime = get_cutoff_datetime(args.before)
    except ValueError as e:
        print(f"Error: {e}")
        return

    print("=" * 70)
    print("Delete Old Media Files")
    print("=" * 70)
    print(f"API Base URL: {BASE_URL}")
    print(f"Cutoff date: {cutoff_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"Mode: {'DELETE' if args.delete else 'DRY RUN'}")
    print("=" * 70)
    print()

    if not args.delete:
        print("⚠ DRY RUN MODE: No data will be deleted. Use --delete to actually delete.")
        print()

    try:
        deleted, failed = delete_old_media_files(
            cutoff_datetime,
            dry_run=not args.delete,
        )

        # Summary
        print()
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        if args.delete:
            print(f"Total deleted: {deleted}")
            print(f"Total failed: {failed}")
        else:
            print("DRY RUN completed. Use --delete flag to actually delete media.")
        print("=" * 70)

    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
