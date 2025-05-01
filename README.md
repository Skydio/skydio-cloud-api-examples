# Skydio Cloud API Example Scripts

This repository contains a collection of example scripts demonstrating how to interact with the [Skydio Cloud API](https://apidocs.skydio.com/) using various programming languages.

Whether you're building new workflows to integrate with Skydio or just exploring what the API can do, these examples are intended to help you get started quickly.

---

## Repository Structure

The examples in this repository are organized by language for clarity and flexibility:

```
examples/
├── python/
│   ├── marker_crud.py
│   ├── live_telemetry.py
│   └── download_media.py
├── javascript/
│   └── media-downloader/
```

Each script is standalone, runnable, and includes inline comments explaining what's happening at each step.
Consult the README for each subdirectory for language- or script-specific usage instructions.

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

---

## Resources

- [Skydio Cloud API Reference](https://apidocs.skydio.com/)
