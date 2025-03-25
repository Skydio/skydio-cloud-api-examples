# Skydio Marker API Utilities

This project provides example Python scripts for interacting with the [Skydio Cloud API](https://apidocs.skydio.com/).

---

## Project Structure

```
python/
├── script_name.py              # Runnable examples; usage instructions are documented in each file
├── utils/
│   ├── __init__.py
│   └── skydio_api_client.py    # Lightweight API client wrapper for Skydio Cloud
├── README.md
└── setup.py (optional)
```

---

## How to run scripts in this directory

1. **Clone this repo**:

```bash
git clone https://github.com/your-org/my_project.git
cd examples/python
```

2. **(Optional) Create and activate a virtual environment**:

```bash
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

3. **Install project packages**:

```bash
pip install -e .
```

---

## Set your API token

You must set the `API_TOKEN` environment variable before running the scripts. In some cases (like RTSP streaming), you might have to also set the `API_TOKEN_ID`.

```bash
export API_TOKEN="your_skydio_api_token"
```

Windows PowerShell:

```powershell
$env:API_TOKEN = "your_skydio_api_token"
```

---

## Running the script

From the project root:

```bash
python path/to/script.py
```

See each script for specific usage instructions.

If you encounter any `ModuleNotFoundError`s, install the missing dependencies with:

```bash
pip install <dependency-name>
```
