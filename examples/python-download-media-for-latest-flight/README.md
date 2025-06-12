# Skydio API Example: Python Download Media for Latest Flight

This script demonstrates how to use the Skydio Cloud API to download media files from the most
recent flight of a given Skydio vehicle. It uses the following endpoints:

- GET /v0/vehicle/{serial}
- GET /v0/flights
- GET /v0/media_files
- GET /v0/media/download/{uuid}
- DELETE /v0/media/{uuid}/delete

## Usage

Follow the instructions in the [README.md](../../README.md) file in the root directory of this repository.

Then run this script with the desired flight ID: Run the script with the desired arguments:

```bash
python main.py [-optional-arguments]
```

For more full details on accepted arguments, run:

```bash
python main.py -h
```
