# server.py
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn

# Create an MCP server
mcp = FastMCP("Agent Observer")


# Add a function for logging agent steps
@mcp.tool()
def log_step(step_name: str, description: str) -> bool:
    """
    Log a step that the agent made

    Args:
        step_name: The name of the step
        description: A description of what happened in this step

    Returns:
        True if logging was successful
    """
    print(f"AGENT STEP: {step_name} - {description}")
    return True


@mcp.tool()
def mark_decision(
    decision_point: str, options: list, chosen_option: str, reasoning: str
) -> bool:
    """
    Mark a decision made by the agent

    Args:
        decision_point: The name/identifier of the decision point
        options: List of options that were available
        chosen_option: The option that was chosen
        reasoning: The reasoning behind the decision

    Returns:
        True if marking was successful
    """
    print(f"AGENT DECISION: {decision_point}")
    print(f"  Options: {', '.join(options)}")
    print(f"  Chosen: {chosen_option}")
    print(f"  Reasoning: {reasoning}")
    return True


@mcp.tool()
def log_tool_call(tool_name: str, arguments: dict, result: str) -> bool:
    """
    Log a tool call made by the agent

    Args:
        tool_name: The name of the tool that was called
        arguments: The arguments passed to the tool
        result: The result returned by the tool

    Returns:
        True if logging was successful
    """
    print(f"TOOL CALL: {tool_name}")
    print(f"  Arguments: {arguments}")
    print(f"  Result: {result}")
    return True


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    mcp_server = mcp._mcp_server  # noqa: WPS437

    import argparse

    parser = argparse.ArgumentParser(description="Run MCP SSE-based server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3001, help="Port to listen on")
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port)
