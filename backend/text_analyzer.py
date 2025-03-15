import asyncio
from typing import List, Dict, Any
from google import genai
from google.genai import types


def init_gemini():
    """Initialize the Gemini API with the API key from environment variables."""

    return genai.Client(
        project="trail-ml-9e15e", location="europe-west2", vertexai=True
    )  # Best pratice :)


# Define the function declarations for Gemini
FUNCTION_DECLARATIONS = [
    types.FunctionDeclaration(
        name="log_step",
        description="Log a step that the agent made",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "step_name": types.Schema(
                    type="STRING", description="The name of the step"
                ),
                "description": types.Schema(
                    type="STRING",
                    description="A description of what happened in this step",
                ),
            },
            required=["step_name", "description"],
        ),
    ),
    types.FunctionDeclaration(
        name="mark_decision",
        description="Mark a decision made by the agent",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "decision_point": types.Schema(
                    type="STRING",
                    description="The name/identifier of the decision point",
                ),
                "options": types.Schema(
                    type="ARRAY",
                    items=types.Schema(type="STRING"),
                    description="List of options that were available",
                ),
                "chosen_option": types.Schema(
                    type="STRING",
                    description="The option that was chosen",
                ),
                "reasoning": types.Schema(
                    type="STRING",
                    description="The reasoning behind the decision",
                ),
            },
            required=["decision_point", "options", "chosen_option", "reasoning"],
        ),
    ),
    types.FunctionDeclaration(
        name="log_tool_call",
        description="Log a tool call made by the agent",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "tool_name": types.Schema(
                    type="STRING",
                    description="The name of the tool that was called",
                ),
                "arguments": types.Schema(
                    type="OBJECT",
                    description="The arguments passed to the tool",
                ),
                "result": types.Schema(
                    type="STRING",
                    description="The result returned by the tool",
                ),
            },
            required=["tool_name", "arguments", "result"],
        ),
    ),
]


async def analyze_text_with_gemini(text: str) -> List[Dict[str, Any]]:
    """
    Analyze a text block using Gemini to extract decision points, options, and reasoning.

    Args:
        text: The text block to analyze

    Returns:
        A list of function calls to be executed
    """
    # Initialize the client
    client = None
    try:
        client = init_gemini()
    except Exception as e:
        raise ValueError(f"Failed to initialize Gemini client: {str(e)}")

    # Prepare the prompt for Gemini
    system_prompt = """
    You are an expert at analyzing text that represents an agent's thinking process.
    Your task is to extract decision points, options considered, chosen options, and reasoning.
    Also identify any steps or tool calls mentioned.
    
    For each decision point, call the mark_decision function.
    For each step, call the log_step function.
    For each tool call, call the log_tool_call function.
    
    Make sure to preserve the hierarchical structure of the thinking process,
    so that parent-child relationships between nodes are maintained.
    """

    contents = text

    # Call Gemini with function calling
    try:
        # Create a Tool object with the function declarations
        tool = types.Tool(function_declarations=FUNCTION_DECLARATIONS)

        response = await client.aio.models.generate_content(
            model="gemini-1.5-pro",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                max_output_tokens=4096,
                tools=[tool],
            ),
        )

        # Extract function calls from the response
        function_calls = []

        # Process the response to extract function calls
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "function_call"):
                    function_call = {
                        "name": part.function_call.name,
                        "args": part.function_call.args,
                    }
                    function_calls.append(function_call)

        return function_calls
    except Exception as e:
        raise ValueError(f"Error calling Gemini API: {str(e)}")


async def execute_mcp_calls(function_calls: List[Dict[str, Any]]):
    """
    Execute the MCP function calls extracted from the text analysis.

    Args:
        function_calls: A list of function calls to execute
    """
    from mcp_server import log_step, mark_decision, log_tool_call

    for call in function_calls:
        name = call["name"]
        args = call["args"]

        if name == "log_step":
            # Call directly without asyncio.to_thread
            log_step(args["step_name"], args["description"])
        elif name == "mark_decision":
            # Call directly without asyncio.to_thread
            mark_decision(
                args["decision_point"],
                args["options"],
                args["chosen_option"],
                args["reasoning"],
            )
        elif name == "log_tool_call":
            # Call directly without asyncio.to_thread
            log_tool_call(args["tool_name"], args["arguments"], args["result"])


async def process_thinking_text(text: str):
    """
    Process a thinking text block to generate and execute MCP calls.

    Args:
        text: The thinking text block to process
    """
    # Analyze the text with Gemini
    function_calls = await analyze_text_with_gemini(text)

    # Execute the MCP calls
    await execute_mcp_calls(function_calls)

    return function_calls


# Synchronous wrapper for the async function
def process_thinking_text_sync(text: str) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for process_thinking_text.

    Args:
        text: The thinking text block to process

    Returns:
        A list of function calls that were executed
    """
    return asyncio.run(process_thinking_text(text))
