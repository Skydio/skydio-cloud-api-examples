"""
Python SDK Generator for Skydio API using openapi-python-client

This script generates a Python SDK from the Skydio OpenAPI specification
using the openapi-python-client library instead of OpenAPI Generator.

Usage:
    export API_TOKEN="your_skydio_api_token"
    python generate_sdk.py
"""

import argparse
import json
import os
import ssl
import subprocess
import sys
import urllib.request
import shutil
from pathlib import Path

from fix_openapi_spec import fix_openapi_spec


def run_command(cmd, cwd=None, check=True):
    """Run a shell command"""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=check, shell=isinstance(cmd, str))
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if check:
            sys.exit(1)
        return e


def download_openapi_spec(api_token, output_dir):
    """Download OpenAPI specification from Skydio API"""
    print("Downloading OpenAPI specification from Skydio API...")

    sdk_dir = Path(output_dir)
    sdk_dir.mkdir(exist_ok=True)

    url = "https://api.skydio.com/api/v0/openapi_spec"
    headers = {"Authorization": api_token, "accept": "application/json"}

    try:
        req = urllib.request.Request(url, headers=headers)

        # Use certifi CA bundle so macOS Python (python.org installs) verifies SSL correctly.
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            print("Error: could not configure SSL trust store.")
            print("Try: pip install certifi")
            raise

        with urllib.request.urlopen(req, context=ctx) as response:
            response_data = response.read().decode("utf-8")

        response_json = json.loads(response_data)

        if isinstance(response_json, dict) and "data" in response_json:
            print("Detected wrapped API response, extracting OpenAPI spec...")
            if "openapi_spec" in response_json["data"]:
                openapi_spec = response_json["data"]["openapi_spec"]
            else:
                print("Error: 'openapi_spec' not found in response data")
                sys.exit(1)
        else:
            print("Detected direct OpenAPI spec response...")
            openapi_spec = response_json

        # Save the original spec for comparison/debugging
        original_spec_file = sdk_dir / "openapi_spec_original.json"
        with open(original_spec_file, "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2)
        print(f"Saved original OpenAPI spec to {original_spec_file}")

        # Apply all fixes to the spec
        openapi_spec = fix_openapi_spec(openapi_spec)

        # Write the modified spec to file
        spec_file = sdk_dir / "openapi_spec.json"
        with open(spec_file, "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2)
        print(f"Saved modified OpenAPI spec to {spec_file}")

        print("Downloaded and cleaned OpenAPI specification successfully")
        return str(spec_file)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error downloading OpenAPI specification: {e}")
        sys.exit(1)


def install_openapi_python_client():
    """Install openapi-python-client if not already installed"""
    print("Checking for openapi-python-client...")

    import importlib.util

    if importlib.util.find_spec("openapi_python_client") is not None:
        print("openapi-python-client is already installed")
    else:
        print("Installing openapi-python-client and certifi...")
        run_command([sys.executable, "-m", "pip", "install", "openapi-python-client", "certifi"])
        print("openapi-python-client installed successfully")


def generate_python_sdk(spec_file, output_dir):
    """Generate Python SDK using openapi-python-client"""
    print("Generating Python SDK with openapi-python-client...")

    sdk_dir = Path(output_dir)
    sdk_dir.mkdir(exist_ok=True)

    # Remove existing generated client if present
    client_dir = sdk_dir / "skydio-client"
    if client_dir.exists():
        print(f"Removing existing client directory: {client_dir}")
        shutil.rmtree(client_dir)

    # Generate the client
    cmd = [
        sys.executable,
        "-m",
        "openapi_python_client",
        "generate",
        "--path",
        spec_file,
        "--output-path",
        str(client_dir),
        "--config",
        str(sdk_dir / "config.yaml"),
    ]

    # Create a config file for openapi-python-client
    config_file = sdk_dir / "config.yaml"
    config_content = """
project_name_override: skydio-client
package_name_override: skydio_client
literal_enums: false
"""
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)

    run_command(cmd)
    print(f"Python SDK generated successfully in {client_dir}/")

    return str(client_dir)


def clean_output_directory(output_dir):
    """Clean up the output directory to start fresh"""
    sdk_dir = Path(output_dir)
    if sdk_dir.exists():
        print(f"Cleaning up existing {output_dir} directory...")
        shutil.rmtree(sdk_dir)
        print(f"Cleaned up {output_dir} directory")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Python SDK for Skydio API using openapi-python-client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  export API_TOKEN="your_skydio_api_token"
  %(prog)s                    # Generate SDK
  %(prog)s --output-dir my_sdk # Generate SDK in custom directory
        """,
    )

    parser.add_argument(
        "--output-dir",
        default="skydio_sdk_generated",
        help="Output directory for generated SDK (default: skydio_sdk_generated)",
    )

    args = parser.parse_args()

    # Get API token from environment variable
    api_token = os.environ.get("API_TOKEN")
    if not api_token:
        print("Error: API_TOKEN environment variable is not set")
        print('Please set it with: export API_TOKEN="your_skydio_api_token"')
        sys.exit(1)

    # Clean up any existing output directory
    clean_output_directory(args.output_dir)

    # Install openapi-python-client if needed
    install_openapi_python_client()

    # Download OpenAPI specification
    spec_file = download_openapi_spec(api_token, args.output_dir)

    # Generate Python SDK
    output_dir = generate_python_sdk(spec_file, args.output_dir)

    print("\n✅ SDK generation completed successfully!")
    print(f"📁 Generated SDK is available in: {output_dir}/")
    print(f"📁 All SDK files are organized in: ./{args.output_dir}/")
    print("📖 Check the generated directory for usage instructions.")
    print("\n💡 To use the SDK, install it with:")
    print(f"   pip install -e {output_dir}")


if __name__ == "__main__":
    main()
