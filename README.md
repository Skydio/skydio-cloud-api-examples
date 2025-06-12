# Skydio Cloud API Example Scripts

This repository contains a collection of example scripts demonstrating how to interact with the [Skydio Cloud API](https://apidocs.skydio.com/) using various programming languages.

Whether you're building new workflows to integrate with Skydio or just exploring what the API can do, these examples are intended to help you get started quickly.

## How to use

The examples in this repository are organized by language for clarity and flexibility.
Each example is in its own folder.

You will need a Skydio API Token, which can be obtained from Integrations settings in https://cloud.skydio.com. The API Token ID can be obtained by clicking details on the API Token.

To get started, follow these steps:

Unix:

```bash
# Clone this repo
git clone https://github.com/Skydio/skydio-cloud-api-examples.git

# Navigate to this repo folder
cd skydio-cloud-api-examples

# Set your Skydio API token
# Your Skydio API token
export API_TOKEN="your_skydio_api_token"
export API_TOKEN_ID="your_skydio_api_token_id"
```

Windows PowerShell:

```powershell
# Clone this repo
git clone https://github.com/Skydio/skydio-cloud-api-examples.git

# Navigate to this repo folder
cd skydio-cloud-api-examples

# Set your Skydio API token
$env:API_TOKEN = "your_skydio_api_token"
$env:API_TOKEN_ID = "your_skydio_api_token_id"
```

Then follow the instructions for the specific language of the example you want to use.

### Python examples

To run a Python example, you need python3 to be installed. Then follow these steps:

Unix:

```bash
# Navigate to the example directory
cd examples/python-<example_name>

# (Optional) Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install project packages
pip install -e .

# Run the script
python main.py
```

Windows PowerShell:

```powershell
# Navigate to the example directory
cd examples\python-<example_name>

# (Optional) Create and activate a virtual environment
python3 -m venv venv
venv\Scripts\activate

# Install project packages
pip install -e .

# Run the script
python main.py
```

See each example's README.md for specific usage instructions.

If you encounter any `ModuleNotFoundError`s, install the missing dependencies with:

```bash
pip install <dependency-name>
```

### Javascript examples

To run a Javascript example, you need Node.js to be installed. Then follow these steps:

Unix:

```bash
# Navigate to the example directory
cd examples/javascript-<example_name>

# Install dependencies
npm install

# Run the script
npm run start
```

Windows PowerShell:

```powershell
# Navigate to the example directory
cd examples\javascript-<example_name>

# Install dependencies
npm install

# Run the script
npm run start
```

See each example's README.md for specific usage instructions.

## Using LLMs to Build Integrations

The Skydio Cloud API is comprehensive — sometimes you might want examples tailored to your specific use case, or just need a faster way to consume the documentation and generate a prototype. An LLM (Large Language Model) like [ChatGPT](https://chat.openai.com) or another AI assistant can be used to:

- Convert an existing script, that already models your use case, to another language
- Generate examples for specific endpoints not included here
- Write integration code for your stack (e.g., Flask, FastAPI, React, Node.js)
- Troubleshoot API request patterns or authentication headers

If using an LLM to develop with the Skydio Cloud API, here are our recommendations.

### Building Context for your LLM

#### Cursor AI

Add our API docs as a Custom Doc in your Cursor settings. To get started, follow the instructions to [create a new Custom Doc](https://docs.cursor.com/context/@-symbols/@-docs), pasting in the Skydio API docs URL (`https://apidocs.skydio.com/`). You can now ask questions about our API and start to generate sample code for your integration.

#### Other LLMs

We recommend pasting the following information into your chat:

- Skydio Cloud API's Open API spec
- The contents of any other page of our docs website that might be relevant to your use case. Of note, [Webhook Request Format](https://apidocs.skydio.com/reference/webhook_request_format), [RTSP Streaming](https://apidocs.skydio.com/reference/rtsp-streaming), and [Live Telemetry](https://apidocs.skydio.com/reference/live-telemetry) are especially useful.

### Examples of sample prompts

```
Write a Python script that consumes live telemetry data from a Skydio vehicle, using a webhook to determine when the websocket is available.
```

```
Write a Python script that, given a vehicle serial, downloads all media for its most recent flight.
```

We’ve seen great results by providing:

- The API endpoint documentation (as recommended above)
- The desired language
- Specific inputs or formats you need, as well as usage preferences (ex: `takes the vehicle_serial as a command line argument`)

Finally, we also recommend using the LLM to help you iterate on the initial code snippet. These are some prompts you can use to fine-tune the results:

```
Can you add error handling to the API requests?
```

```
Update the script to read the API token from an environment variable instead of using a hard-coded global variable.
```

## Resources

- [Skydio Cloud API Reference](https://apidocs.skydio.com/)
