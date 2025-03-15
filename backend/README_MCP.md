# MCP Server for Agent Observer

This document explains how to use the MCP (Machine Communication Protocol) server implemented in this project for tracking agent actions.

## Overview

The MCP server provides tools for logging agent steps, decisions, and tool calls. These logs are stored in the database as nodes and can be visualized in the frontend.

## Available Tools

The MCP server provides the following tools:

1. **log_step** - Log a step that the agent made
   - Parameters:
     - `step_name`: The name of the step
     - `description`: A description of what happened in this step

2. **mark_decision** - Mark a decision made by the agent
   - Parameters:
     - `decision_point`: The name/identifier of the decision point
     - `options`: List of options that were available
     - `chosen_option`: The option that was chosen
     - `reasoning`: The reasoning behind the decision

3. **log_tool_call** - Log a tool call made by the agent
   - Parameters:
     - `tool_name`: The name of the tool that was called
     - `arguments`: The arguments passed to the tool
     - `result`: The result returned by the tool

## How to Use

### Starting the Server

The MCP server is automatically started when you run the main FastAPI application:

```bash
cd backend
python main.py
```

This will start the server on port 8000, with the MCP endpoint available at `/mcp`.

### Testing the Server

You can test the MCP server using the provided test script:

```bash
cd backend
python test_mcp.py
```

This will send test requests to the MCP server and print the responses.

### Using the MCP Tools in Your Agent

To use the MCP tools in your agent, you need to send JSON-RPC requests to the MCP server. Here's an example in Python:

```python
import requests
import json

def log_step(step_name, description):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "log_step",
        "params": {
            "step_name": step_name,
            "description": description
        }
    }
    
    response = requests.post("http://localhost:8000/mcp/messages", json=payload)
    return response.json()

# Example usage
log_step("Initialize", "Agent initialized and ready to process tasks")
```

## Integration with Frontend

The MCP server creates nodes in the database for each log, decision, or tool call. These nodes are automatically published to subscribers through GraphQL subscriptions, allowing the frontend to display them in real-time.

## Customization

If you need to add more tools or modify the existing ones, you can edit the `mcp_server.py` file. Make sure to update the node model if necessary to accommodate new types of data. 