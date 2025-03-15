# Agent Observer with SSE

This project implements a Server-Sent Events (SSE) based server for agent observation and interaction.

## Components

- `server.py`: The main server that provides SSE endpoints and agent observation tools
- `test_sse_client.py`: A test client to demonstrate SSE connection and interaction
- `test_sse.sh`: Shell script for testing SSE functionality
- `test_direct.sh`: Shell script for testing tools directly without SSE

## Setup

1. Install the required dependencies:

```bash
pip install httpx uvicorn starlette
```

## Running the Server

Start the SSE server with:

```bash
python server.py
```

By default, the server runs on `0.0.0.0:8080`. You can customize the host and port:

```bash
python server.py --host 127.0.0.1 --port 9000
```

## Testing with the Client

The test client can be used to verify the SSE connection and tool functionality:

```bash
python test_sse_client.py
```

### Client Options

- `--host`: Server host (default: localhost)
- `--port`: Server port (default: 8080)
- `--mode`: Operation mode (choices: listen, send, both; default: both)

Examples:

```bash
# Just listen for events
python test_sse_client.py --mode listen

# Just send a test message
python test_sse_client.py --mode send

# Connect to a custom server
python test_sse_client.py --host 192.168.1.100 --port 9000
```

## Testing with Shell Scripts

### Testing SSE Functionality

Use the `test_sse.sh` script to test SSE functionality from the command line:

```bash
# Show help
./test_sse.sh

# Listen for SSE events
./test_sse.sh localhost 8080 listen

# Send a log_step message
./test_sse.sh localhost 8080 log
```

### Testing Tools Directly (Without SSE)

Use the `test_direct.sh` script to test tools directly without using SSE:

```bash
# Show help
./test_direct.sh

# Call log_step tool
./test_direct.sh localhost 8080 log

# Call mark_decision tool
./test_direct.sh localhost 8080 decision

# Call log_tool_call tool
./test_direct.sh localhost 8080 tool
```

## Available Tools

The server provides the following tools for agent observation:

1. `log_step`: Log a step that the agent made
2. `mark_decision`: Mark a decision made by the agent
3. `log_tool_call`: Log a tool call made by the agent

## SSE Endpoints

- `/sse`: The SSE connection endpoint
- `/messages/`: Endpoint for posting messages to the SSE stream

## Direct API Endpoints

When not using SSE, you can call the tools directly via these endpoints:

- `/api/v1/tools/log_step`: Log a step
- `/api/v1/tools/mark_decision`: Mark a decision
- `/api/v1/tools/log_tool_call`: Log a tool call

## Protocol

The SSE communication uses a simple JSON-based protocol:

- Requests have the format:
  ```json
  {
    "type": "request",
    "id": "unique-request-id",
    "method": "tool",
    "params": {
      "method": "tool_name",
      "params": {
        "param1": "value1",
        "param2": "value2"
      }
    }
  }
  ```

- Responses have the format:
  ```json
  {
    "type": "response",
    "id": "unique-request-id",
    "result": true
  }
  ```
