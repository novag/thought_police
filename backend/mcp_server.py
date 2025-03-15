from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
import json
from sqlalchemy.orm import Session
from models import Node, NodeType, Trace
from database import get_db
import asyncio
from schema import publish_node, Node as NodeSchema

# Create an MCP server
mcp = FastMCP("Agent Observer")

# Global variable to store the current trace ID
current_trace_id = None

# Global variable to store the last node ID (for parent-child relationships)
last_node_id = None

# Function to get or create a trace
def get_or_create_trace(db: Session, name: str = "Agent Trace", description: str = "Trace of agent actions"):
    global current_trace_id
    global last_node_id
    
    # If we already have a trace ID, use it
    if current_trace_id:
        trace = db.query(Trace).filter(Trace.id == current_trace_id).first()
        if trace:
            return trace
    
    # Create a new trace
    trace = Trace(name=name, description=description)
    db.add(trace)
    db.commit()
    db.refresh(trace)
    
    # Store the trace ID for future use
    current_trace_id = trace.id
    
    # Reset the last node ID when creating a new trace
    last_node_id = None
    
    return trace

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
    global last_node_id
    print(f"AGENT STEP: {step_name} - {description}")
    
    # Get a database session
    db = next(get_db())
    
    # Get or create a trace
    trace = get_or_create_trace(db)
    
    # Create a node for the step
    node = Node(
        type=NodeType.LOGGING,
        label=step_name,
        content=description,
        trace_id=trace.id,
        log_level="INFO",
        parent_id=last_node_id  # Set the parent_id to the last node created
    )
    
    db.add(node)
    db.commit()
    db.refresh(node)
    
    # Update the last node ID
    last_node_id = node.id
    
    # Create a node schema object for publishing
    node_schema = NodeSchema.from_db_model(node, db)
    
    # Publish the node asynchronously
    asyncio.create_task(publish_node(node_schema))
    
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
    global last_node_id
    print(f"AGENT DECISION: {decision_point}")
    print(f"  Options: {', '.join(options)}")
    print(f"  Chosen: {chosen_option}")
    print(f"  Reasoning: {reasoning}")
    
    # Get a database session
    db = next(get_db())
    
    # Get or create a trace
    trace = get_or_create_trace(db)
    
    # Create a node for the decision
    content = f"Options: {', '.join(options)}\nReasoning: {reasoning}"
    node = Node(
        type=NodeType.DECISION,
        label=decision_point,
        content=content,
        trace_id=trace.id,
        decision_outcome=chosen_option,
        parent_id=last_node_id  # Set the parent_id to the last node created
    )
    
    db.add(node)
    db.commit()
    db.refresh(node)
    
    # Update the last node ID
    last_node_id = node.id
    
    # Create a node schema object for publishing
    node_schema = NodeSchema.from_db_model(node, db)
    
    # Publish the node asynchronously
    asyncio.create_task(publish_node(node_schema))
    
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
    global last_node_id
    print(f"TOOL CALL: {tool_name}")
    print(f"  Arguments: {arguments}")
    print(f"  Result: {result}")
    
    # Get a database session
    db = next(get_db())
    
    # Get or create a trace
    trace = get_or_create_trace(db)
    
    # Create a node for the tool call
    content = f"Arguments: {json.dumps(arguments)}\nResult: {result}"
    node = Node(
        type=NodeType.TOOL_CALL,
        label=f"Tool Call: {tool_name}",
        content=content,
        trace_id=trace.id,
        tool_name=tool_name,
        parent_id=last_node_id  # Set the parent_id to the last node created
    )
    
    db.add(node)
    db.commit()
    db.refresh(node)
    
    # Update the last node ID
    last_node_id = node.id
    
    # Create a node schema object for publishing
    node_schema = NodeSchema.from_db_model(node, db)
    
    # Publish the node asynchronously
    asyncio.create_task(publish_node(node_schema))
    
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


def get_mcp_app():
    """Get the MCP Starlette app for mounting in the main FastAPI app."""
    mcp_server = mcp._mcp_server  # noqa: WPS437
    return create_starlette_app(mcp_server, debug=True)


if __name__ == "__main__":
    # This allows running the MCP server standalone for testing
    mcp_server = mcp._mcp_server  # noqa: WPS437

    import argparse

    parser = argparse.ArgumentParser(description="Run MCP SSE-based server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3001, help="Port to listen on")
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port) 