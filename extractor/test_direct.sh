#!/bin/bash
# Script to test FastMCP server tools directly (without SSE)

HOST=${1:-localhost}
PORT=${2:-8080}
BASE_URL="http://${HOST}:${PORT}"

function show_help() {
  echo "FastMCP Direct Tool Test Script"
  echo "Usage: $0 [host] [port] [command]"
  echo ""
  echo "Commands:"
  echo "  log       - Call log_step tool"
  echo "  decision  - Call mark_decision tool"
  echo "  tool      - Call log_tool_call tool"
  echo ""
  echo "Examples:"
  echo "  $0                     - Show this help"
  echo "  $0 localhost 8080 log  - Call log_step on default server"
}

function call_log_step() {
  echo "Calling log_step tool at ${BASE_URL}/api/v1/tools/log_step"
  curl -X POST "${BASE_URL}/api/v1/tools/log_step" \
    -H "Content-Type: application/json" \
    -d '{
      "step_name": "Direct CLI Test",
      "description": "Testing direct tool call from CLI"
    }'
  echo ""
}

function call_mark_decision() {
  echo "Calling mark_decision tool at ${BASE_URL}/api/v1/tools/mark_decision"
  curl -X POST "${BASE_URL}/api/v1/tools/mark_decision" \
    -H "Content-Type: application/json" \
    -d '{
      "decision_point": "Direct CLI Test",
      "options": ["Option A", "Option B", "Option C"],
      "chosen_option": "Option B",
      "reasoning": "Testing from CLI without SSE"
    }'
  echo ""
}

function call_log_tool_call() {
  echo "Calling log_tool_call tool at ${BASE_URL}/api/v1/tools/log_tool_call"
  curl -X POST "${BASE_URL}/api/v1/tools/log_tool_call" \
    -H "Content-Type: application/json" \
    -d '{
      "tool_name": "test_tool",
      "arguments": {"arg1": "value1", "arg2": "value2"},
      "result": "Success from direct CLI test"
    }'
  echo ""
}

# Process command
COMMAND=${3:-"help"}

case $COMMAND in
  "log")
    call_log_step
    ;;
  "decision")
    call_mark_decision
    ;;
  "tool")
    call_log_tool_call
    ;;
  *)
    show_help
    ;;
esac 