#!/usr/bin/env python3
"""
Python SDK Generator for Skydio API

This script generates a Python SDK from the Skydio OpenAPI specification.
It supports both pre-built JAR (default, faster) and building from source options.
"""

import argparse
import os
import subprocess
import sys
import urllib.request
import shutil
from pathlib import Path


def find_java_home():
    """Find and set JAVA_HOME on macOS"""
    try:
        result = subprocess.run(
            ["/usr/libexec/java_home"], capture_output=True, text=True, check=True
        )
        java_home = result.stdout.strip()
        os.environ["JAVA_HOME"] = java_home
        print(f"Using Java at: {java_home}")
        return java_home
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Could not find a valid Java installation")
        sys.exit(1)


def download_file(url, filename):
    """Download a file from URL with progress indication"""
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        print(f"Downloaded {filename} successfully")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        sys.exit(1)


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


def setup_openapi_generator(build_from_source=False):
    """Setup OpenAPI Generator either from source or pre-built JAR"""

    # Create main skydio_sdk_generated directory
    sdk_dir = Path("skydio_sdk_generated")
    sdk_dir.mkdir(exist_ok=True)

    if build_from_source:
        print("Building OpenAPI Generator from source...")

        # Clone or use existing repository
        openapi_gen_dir = sdk_dir / "openapi-generator"
        if openapi_gen_dir.exists():
            print(
                "OpenAPI Generator directory already exists, using existing installation..."
            )
        else:
            print("Cloning OpenAPI Generator...")
            run_command(
                [
                    "git",
                    "clone",
                    "https://github.com/openapitools/openapi-generator",
                    str(openapi_gen_dir),
                ]
            )

        # Build from source
        print("Building OpenAPI Generator (this may take several minutes)...)")
        run_command(["./mvnw", "clean", "package"], cwd=str(openapi_gen_dir))

        jar_path = (
            openapi_gen_dir
            / "modules/openapi-generator-cli/target/openapi-generator-cli.jar"
        )

    else:
        print("Using pre-built OpenAPI Generator JAR...")

        # Create openapi-generator-cli directory inside skydio_sdk_generated
        cli_dir = sdk_dir / "openapi-generator-cli"
        cli_dir.mkdir(exist_ok=True)

        # Download pre-built JAR into the directory
        version = "7.2.0"
        jar_filename = f"openapi-generator-cli-{version}.jar"
        jar_path = cli_dir / jar_filename

        if not jar_path.exists():
            jar_url = f"https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/{version}/{jar_filename}"
            download_file(jar_url, str(jar_path))
        else:
            print("OpenAPI Generator CLI JAR already exists, using existing file...")

        jar_path = str(jar_path)

    return jar_path


def download_openapi_spec(api_token):
    """Download OpenAPI specification from Skydio API"""
    print("Downloading OpenAPI specification from Skydio API...")

    import urllib.request
    import urllib.parse
    import json

    # Ensure skydio_sdk_generated directory exists
    sdk_dir = Path("skydio_sdk_generated")
    sdk_dir.mkdir(exist_ok=True)

    url = "https://api.skydio.com/api/v0/openapi_spec"
    headers = {"Authorization": api_token, "accept": "application/json"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode("utf-8")

        # Parse the JSON response
        response_json = json.loads(response_data)

        # Check if this is a wrapped response with 'data' field
        if isinstance(response_json, dict) and "data" in response_json:
            print("Detected wrapped API response, extracting OpenAPI spec...")
            if "openapi_spec" in response_json["data"]:
                openapi_spec = response_json["data"]["openapi_spec"]
            else:
                print("Error: 'openapi_spec' not found in response data")
                sys.exit(1)
        else:
            # Assume it's already the OpenAPI spec directly
            print("Detected direct OpenAPI spec response...")
            openapi_spec = response_json

        # Write the extracted OpenAPI spec to file inside skydio_sdk_generated
        spec_file = sdk_dir / "openapi_spec.json"
        with open(spec_file, "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2)

        print("Downloaded and extracted OpenAPI specification successfully")
        return str(spec_file)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error downloading OpenAPI specification: {e}")
        sys.exit(1)


def generate_python_sdk(jar_path, spec_file):
    """Generate Python SDK using OpenAPI Generator"""
    print("Generating Python SDK...")

    # Ensure skydio_sdk_generated directory exists
    sdk_dir = Path("skydio_sdk_generated")
    sdk_dir.mkdir(exist_ok=True)

    # Output directory inside skydio_sdk_generated
    output_dir = sdk_dir / "python_api_client"

    cmd = [
        "java",
        "-jar",
        jar_path,
        "generate",
        "--input-spec",
        spec_file,
        "--generator-name",
        "python",
        "--output",
        str(output_dir),
        "--global-property",
        "skipFormModel=false",
        "--additional-properties",
        "generateSourceCodeOnly=false,packageName=skydio_sdk",
        "--type-mappings",
        "file=str",  # Map file type to string to avoid the error
    ]

    run_command(cmd)
    print(f"Python SDK generated successfully in {output_dir}/")
    return str(output_dir)


def install_python_sdk(output_dir):
    """Install the generated Python SDK"""
    print("Installing Python SDK...")

    # Change to the SDK directory and install
    sdk_setup_dir = Path(output_dir)

    cmd = [sys.executable, "-m", "pip", "install", "-e", ".", "--user"]

    run_command(cmd, cwd=str(sdk_setup_dir))
    print("Python SDK installed successfully!")


def uninstall_python_sdk():
    """Uninstall the generated Python SDK if it exists"""
    print("Uninstalling existing Python SDK (if present)...")

    # The package name is 'skydio-sdk' (pip normalizes underscores to hyphens)
    cmd = [sys.executable, "-m", "pip", "uninstall", "skydio-sdk", "-y"]

    # Use check=False to avoid crashing if package is not installed
    run_command(cmd, check=False)
    print("Uninstall step completed")


def clean_skydio_sdk_generated():
    """Clean up the skydio_sdk_generated directory to start fresh"""
    sdk_dir = Path("skydio_sdk_generated")
    if sdk_dir.exists():
        print("Cleaning up existing skydio_sdk_generated directory...")
        shutil.rmtree(sdk_dir)
        print("Cleaned up skydio_sdk_generated directory")


def patch_sdk_for_data_unwrapping(output_dir):
    """
    Patch the generated SDK to automatically unwrap responses from the 'data' field.

    Skydio API wraps all responses in a JSON payload with the actual response in the 'data' field.
    This function modifies the ApiClient's deserialize method to handle this automatically.
    """
    print("Patching SDK to unwrap 'data' field from responses...")

    api_client_path = Path(output_dir) / "skydio_sdk" / "api_client.py"

    if not api_client_path.exists():
        print(f"Warning: Could not find api_client.py at {api_client_path}")
        return

    # Read the current content
    with open(api_client_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the deserialize method and patch it
    # We'll add logic to unwrap the 'data' field if it exists
    patch_code = '''
    def __deserialize_data_wrapper(self, response_data, response_type):
        """
        Unwrap Skydio API response wrapper if present.
        Skydio API wraps responses in: {"data": {...actual response...}}
        """
        if isinstance(response_data, dict) and "data" in response_data:
            # This looks like a Skydio wrapper, unwrap it
            return response_data["data"]
        return response_data
'''

    # Insert the helper method before the deserialize method
    if "def __deserialize(" in content:
        # Add the helper method
        content = content.replace(
            "    def __deserialize(", patch_code + "\n    def __deserialize("
        )

        # Now modify the __deserialize method to use the helper
        # Find where response_data is first used in deserialization
        # Typically it's after response_data = self.__deserialize_primitive(data, klass)
        # We need to wrap it after getting the data but before type checking

        # Look for the pattern where we have the data and are about to deserialize it
        old_pattern = '''    def __deserialize(self, data, klass):
        """Deserializes dict, list, str into an object.

        :param data: dict, list or str.
        :param klass: class literal, or string of class name.

        :return: object.
        """
        if data is None:
            return None'''

        new_pattern = '''    def __deserialize(self, data, klass):
        """Deserializes dict, list, str into an object.

        :param data: dict, list or str.
        :param klass: class literal, or string of class name.

        :return: object.
        """
        # Unwrap Skydio API response wrapper if present
        data = self.__deserialize_data_wrapper(data, klass)
        
        if data is None:
            return None'''

        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)

            # Write the patched content back
            with open(api_client_path, "w", encoding="utf-8") as f:
                f.write(content)

            print("✅ Successfully patched SDK to unwrap 'data' field")
        else:
            print(
                "⚠️  Warning: Could not find expected deserialize method pattern to patch"
            )
    else:
        print("⚠️  Warning: Could not find __deserialize method in api_client.py")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Python SDK for Skydio API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  export API_TOKEN="your_skydio_api_token"
  %(prog)s                    # Use pre-built JAR (faster)
  %(prog)s --build-from-source # Build from source
        """,
    )

    parser.add_argument(
        "--build-from-source",
        action="store_true",
        help="Build OpenAPI Generator from source (slower but latest version)",
    )

    args = parser.parse_args()

    # Get API token from environment variable
    api_token = os.environ.get("API_TOKEN")
    if not api_token:
        print("Error: API_TOKEN environment variable is not set")
        print('Please set it with: export API_TOKEN="your_skydio_api_token"')
        sys.exit(1)

    # # Uninstall any existing SDK installation
    # uninstall_python_sdk()

    # Clean up any existing skydio_sdk_generated directory
    clean_skydio_sdk_generated()

    # Set up Java environment
    find_java_home()

    # Setup OpenAPI Generator
    jar_path = setup_openapi_generator(args.build_from_source)

    # Download OpenAPI specification
    spec_file = download_openapi_spec(api_token)

    # Generate Python SDK
    output_dir = generate_python_sdk(jar_path, spec_file)

    # Patch the SDK to unwrap 'data' field from responses
    patch_sdk_for_data_unwrapping(output_dir)

    # # Install the generated SDK
    # install_python_sdk(output_dir)

    print("\n✅ SDK generation completed successfully!")
    print(f"📁 Generated SDK is available in: {output_dir}/")
    print("📁 All SDK files are organized in: ./skydio_sdk_generated/")
    print("📖 Check the README.md in the generated directory for usage instructions.")
    print(
        "\n🔧 The SDK has been patched to automatically unwrap the 'data' field from API responses."
    )


if __name__ == "__main__":
    main()
