#!/bin/bash
# Simple script to test SSE server from command line

HOST=${1:-localhost}
PORT=${2:-8080}
BASE_URL="http://${HOST}:${PORT}"

function show_help() {
  echo "SSE Server Test Script"
  echo "Usage: $0 [host] [port] [command]"
  echo ""
  echo "Commands:"
  echo "  listen    - Connect to SSE stream and listen for events"
  echo "  log       - Send a log_step message"
  echo "  decision  - Send a mark_decision message"
  echo "  tool      - Send a log_tool_call message"
  echo ""
  echo "Examples:"
  echo "  $0                     - Use default host/port"
  echo "  $0 192.168.1.100 9000  - Use custom host/port"
  echo "  $0 localhost 8080 log  - Send log message to default server"
}

function listen_for_events() {
  echo "Connecting to SSE stream at ${BASE_URL}/sse"
  echo "Press Ctrl+C to stop listening"
  echo ""
  
  if command -v jq &> /dev/null; then
    # Use jq for pretty-printing if available
    curl -N "${BASE_URL}/sse" | while read line; do
      if [[ $line == data:* ]]; then
        echo $line | sed 's/^data: //' | jq
      else
        echo $line
      fi
    done
  else
    # Plain output if jq is not available
    curl -N "${BASE_URL}/sse"
  fi
}

function send_log_step() {
  echo "Sending log_step message to ${BASE_URL}/messages/"
  curl -X POST "${BASE_URL}/messages/" \
    -H "Content-Type: application/json" \
    -d '{
      "type": "request",
      "id": "cli-test-log",
      "method": "tool",
      "params": {
        "method": "log_step",
        "params": {
          "step_name": "CLI Test",
          "description": "Testing from command line"
        }
      }
    }'
  echo ""
}

function send_mark_decision() {
  echo "Sending mark_decision message to ${BASE_URL}/messages/"
  curl -X POST "${BASE_URL}/messages/" \
    -H "Content-Type: application/json" \
    -d '{
      "type": "request",
      "id": "cli-test-decision",
      "method": "tool",
      "params": {
        "method": "mark_decision",
        "params": {
          "decision_point": "CLI Test Decision",
          "options": ["Option A", "Option B", "Option C"],
          "chosen_option": "Option B",
          "reasoning": "Testing decision marking from CLI"
        }
      }
    }'
  echo ""
}

function send_log_tool_call() {
  echo "Sending log_tool_call message to ${BASE_URL}/messages/"
  curl -X POST "${BASE_URL}/messages/" \
    -H "Content-Type: application/json" \
    -d '{
      "type": "request",
      "id": "cli-test-tool",
      "method": "tool",
      "params": {
        "method": "log_tool_call",
        "params": {
          "tool_name": "test_tool",
          "arguments": {"arg1": "value1", "arg2": "value2"},
          "result": "Success from CLI test"
        }
      }
    }'
  echo ""
}

# Process command
COMMAND=${3:-"help"}

case $COMMAND in
  "listen")
    listen_for_events
    ;;
  "log")
    send_log_step
    ;;
  "decision")
    send_mark_decision
    ;;
  "tool")
    send_log_tool_call
    ;;
  *)
    show_help
    ;;
esac 