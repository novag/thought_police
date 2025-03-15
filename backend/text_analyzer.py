import asyncio
from typing import List, Dict, Any
from google import genai
from google.genai import types
import json


def init_gemini():
    """Initialize the Gemini API with the API key from environment variables."""

    return genai.Client(
        project="trail-ml-9e15e", location="us-central1", vertexai=True
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
    types.FunctionDeclaration(
        name="get_previous_steps",
        description="Retrieve the previous steps in the current branch of execution",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "num_steps": types.Schema(
                    type="INTEGER",
                    description="The number of previous steps to retrieve (default: 5)",
                ),
            },
            required=[],
        ),
    ),
    types.FunctionDeclaration(
        name="set_current_node",
        description="Set the current node to a specific node ID, effectively moving back in the branch",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "node_id": types.Schema(
                    type="INTEGER",
                    description="The ID of the node to set as the current node",
                ),
            },
            required=["node_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="go_back_steps",
        description="Move back a specific number of steps in the current branch",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "num_steps": types.Schema(
                    type="INTEGER",
                    description="The number of steps to go back (default: 1)",
                ),
            },
            required=[],
        ),
    ),
]


class IncrementalTextAnalyzer:
    """
    A class that analyzes text incrementally, building a decision tree and graph
    as new text chunks are added.
    """

    def __init__(self, session_id: str = "default_session"):
        """
        Initialize the incremental text analyzer.

        Args:
            session_id: A unique identifier for this analysis session
        """
        self.session_id = session_id
        self.text_buffer = ""
        self.processed_text = ""
        self.client = None
        self.last_function_calls = []
        self.initialized = False

    async def initialize(self):
        """Initialize the Gemini client."""
        if not self.initialized:
            try:
                self.client = init_gemini()
                self.initialized = True
            except Exception as e:
                raise ValueError(f"Failed to initialize Gemini client: {str(e)}")

    async def add_text_chunk(self, text_chunk: str) -> List[Dict[str, Any]]:
        """
        Add a new chunk of text to the analyzer and process it.

        Args:
            text_chunk: The new chunk of text to analyze

        Returns:
            A list of function calls that were executed
        """
        try:
            await self.initialize()

            # Add the new chunk to the buffer
            self.text_buffer += text_chunk

            # Process the updated buffer
            function_calls = await self._process_current_buffer()

            # Execute the MCP calls
            await execute_mcp_calls(function_calls)

            # Store the function calls for reference
            self.last_function_calls = function_calls

            return function_calls
        except Exception as e:
            print(f"Error in add_text_chunk: {str(e)}")
            # Return empty list instead of propagating the exception
            return []

    async def _process_current_buffer(self) -> List[Dict[str, Any]]:
        """
        Process the current text buffer to extract decision points, steps, and tool calls.

        Returns:
            A list of function calls to be executed
        """
        system_prompt = """
        You are an expert at analyzing text that represents an agent's thinking process.
        Your task is to extract decision points, options considered, chosen options, and reasoning.
        Also identify any steps or tool calls mentioned.
        
        For each decision point, call the mark_decision function.
        For each step, call the log_step function.
        For each tool call, call the log_tool_call function.
        
        Make sure to preserve the hierarchical structure of the thinking process,
        so that parent-child relationships between nodes are maintained.
        
        IMPORTANT: You are receiving text incrementally. Focus on analyzing NEW information
        that hasn't been processed before. Don't repeat function calls for content you've
        already analyzed.
        """

        # Add context about what has been processed already
        if self.processed_text:
            context = f"""
            PREVIOUSLY PROCESSED TEXT:
            ```
            {self.processed_text}
            ```
            
            NEW TEXT TO ANALYZE:
            ```
            {self.text_buffer}
            ```
            
            Only analyze the NEW TEXT. Do not repeat function calls for content in the PREVIOUSLY PROCESSED TEXT.
            """
            contents = context
        else:
            contents = self.text_buffer

        # Call Gemini with function calling
        try:
            # Create a Tool object with the function declarations
            tool = types.Tool(function_declarations=FUNCTION_DECLARATIONS)

            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash-lite",
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
                    if (
                        hasattr(part, "function_call")
                        and part.function_call is not None
                    ):
                        try:
                            function_call = {
                                "name": part.function_call.name,
                                "args": part.function_call.args,
                            }
                            function_calls.append(function_call)
                        except AttributeError as attr_err:
                            print(
                                f"Warning: Malformed function call in response: {attr_err}"
                            )
                            # Continue processing other parts instead of failing

            # Update the processed text to include the current buffer
            self.processed_text += self.text_buffer
            self.text_buffer = ""  # Clear the buffer after processing

            return function_calls
        except Exception as e:
            print(f"Error processing text with Gemini: {str(e)}")
            print(f"Text buffer that caused the error: {self.text_buffer[:100]}...")

            # Don't lose the text buffer on error
            # Instead, keep it for the next attempt or manual inspection

            # Return empty list of function calls
            return []

    async def reset(self):
        """Reset the analyzer state."""
        self.text_buffer = ""
        self.processed_text = ""
        self.last_function_calls = []


async def execute_mcp_calls(function_calls: List[Dict[str, Any]]):
    """
    Execute the MCP function calls extracted from the text analysis.

    Args:
        function_calls: A list of function calls to execute
    """
    if not function_calls:
        # No function calls to execute
        return

    try:
        from mcp_server import (
            log_step,
            mark_decision,
            log_tool_call,
            get_previous_steps,
            set_current_node,
            go_back_steps,
        )
    except ImportError as e:
        print(f"Warning: Could not import MCP functions: {str(e)}")
        print("MCP calls will not be executed.")
        return

    for call in function_calls:
        try:
            name = call.get("name")
            args = call.get("args", {})

            if not name or not args:
                print(f"Warning: Invalid function call format: {call}")
                continue

            if name == "log_step":
                if "step_name" in args and "description" in args:
                    log_step(args["step_name"], args["description"])
                else:
                    print(f"Warning: Missing required arguments for log_step: {args}")
            elif name == "mark_decision":
                if all(
                    k in args
                    for k in ["decision_point", "options", "chosen_option", "reasoning"]
                ):
                    mark_decision(
                        args["decision_point"],
                        args["options"],
                        args["chosen_option"],
                        args["reasoning"],
                    )
                else:
                    print(
                        f"Warning: Missing required arguments for mark_decision: {args}"
                    )
            elif name == "log_tool_call":
                if all(k in args for k in ["tool_name", "arguments", "result"]):
                    log_tool_call(args["tool_name"], args["arguments"], args["result"])
                else:
                    print(
                        f"Warning: Missing required arguments for log_tool_call: {args}"
                    )
            elif name == "get_previous_steps":
                num_steps = args.get("num_steps", 5)
                get_previous_steps(num_steps)
            elif name == "set_current_node":
                if "node_id" in args:
                    set_current_node(args["node_id"])
                else:
                    print(
                        f"Warning: Missing required arguments for set_current_node: {args}"
                    )
            elif name == "go_back_steps":
                num_steps = args.get("num_steps", 1)
                go_back_steps(num_steps)
            else:
                print(f"Warning: Unknown function call: {name}")
        except Exception as e:
            print(
                f"Error executing function call {call.get('name', 'unknown')}: {str(e)}"
            )
            # Continue with the next function call instead of failing


# Legacy functions for backward compatibility
async def analyze_text_with_gemini(text: str) -> List[Dict[str, Any]]:
    """
    Analyze a text block using Gemini to extract decision points, options, and reasoning.

    This is a legacy function maintained for backward compatibility.

    Args:
        text: The text block to analyze

    Returns:
        A list of function calls to be executed
    """
    analyzer = IncrementalTextAnalyzer()
    await analyzer.initialize()
    return await analyzer.add_text_chunk(text)


async def process_thinking_text(text: str):
    """
    Process a thinking text block to generate and execute MCP calls.

    This is a legacy function maintained for backward compatibility.

    Args:
        text: The thinking text block to process
    """
    analyzer = IncrementalTextAnalyzer()
    return await analyzer.add_text_chunk(text)


# Synchronous wrapper for the async function
def process_thinking_text_sync(text: str) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for process_thinking_text.

    This is a legacy function maintained for backward compatibility.

    Args:
        text: The thinking text block to process

    Returns:
        A list of function calls that were executed
    """
    return asyncio.run(process_thinking_text(text))


# Synchronous wrapper for the incremental analyzer
class SyncIncrementalTextAnalyzer:
    """
    A synchronous wrapper for the IncrementalTextAnalyzer class.
    """

    def __init__(self, session_id: str = "default_session"):
        """Initialize the synchronous incremental text analyzer."""
        self.async_analyzer = IncrementalTextAnalyzer(session_id)
        # Initialize in a safe way that works both inside and outside event loops
        self._safe_initialize()

    def _safe_initialize(self):
        """Safely initialize the async analyzer without using asyncio.run()."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()

            # Check if we're in a running event loop
            if loop.is_running():
                # Create a new loop for initialization
                new_loop = asyncio.new_event_loop()
                try:
                    # Run the initialization in the new loop
                    new_loop.run_until_complete(self.async_analyzer.initialize())
                finally:
                    # Clean up the new loop
                    new_loop.close()
            else:
                # We can use the existing loop
                loop.run_until_complete(self.async_analyzer.initialize())
        except RuntimeError:
            # If we can't get an event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.async_analyzer.initialize())
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    def add_text_chunk(self, text_chunk: str) -> List[Dict[str, Any]]:
        """
        Add a new chunk of text to the analyzer and process it.

        Args:
            text_chunk: The new chunk of text to analyze

        Returns:
            A list of function calls that were executed
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()

            # Check if we're in a running event loop
            if loop.is_running():
                # We're in a running event loop, create a new task
                # This is a workaround and might not work in all cases
                print(
                    "Warning: Running in an existing event loop. Results may be incomplete."
                )
                # Return empty results to avoid blocking
                return []
            else:
                # We can use the existing loop
                return loop.run_until_complete(
                    self.async_analyzer.add_text_chunk(text_chunk)
                )
        except RuntimeError:
            # If we can't get an event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.async_analyzer.add_text_chunk(text_chunk)
                )
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    def reset(self):
        """Reset the analyzer state."""
        self.text_buffer = ""
        self.processed_text = ""
        self.last_function_calls = []


# Define the updated function declarations for Gemini with navigation capabilities
NAVIGATION_FUNCTION_DECLARATIONS = FUNCTION_DECLARATIONS + [
    types.FunctionDeclaration(
        name="get_previous_steps",
        description="Retrieve the previous steps in the current branch of execution",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "num_steps": types.Schema(
                    type="INTEGER",
                    description="The number of previous steps to retrieve (default: 5)",
                ),
            },
            required=[],
        ),
    ),
    types.FunctionDeclaration(
        name="set_current_node",
        description="Set the current node to a specific node ID, effectively moving back in the branch",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "node_id": types.Schema(
                    type="INTEGER",
                    description="The ID of the node to set as the current node",
                ),
            },
            required=["node_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="go_back_steps",
        description="Move back a specific number of steps in the current branch",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "num_steps": types.Schema(
                    type="INTEGER",
                    description="The number of steps to go back (default: 1)",
                ),
            },
            required=[],
        ),
    ),
]


class AgentLoopController:
    """
    A meta-agent controller that analyzes and builds a graph of another agent's actions.

    This class uses Gemini 2.0 to analyze the text/actions of a base agent, build a graph
    representation of its decision process, and navigate through this graph to better
    understand and visualize the base agent's reasoning.
    """

    def __init__(self, session_id: str = "default_session"):
        """
        Initialize the meta-agent controller.

        Args:
            session_id: A unique identifier for this analysis session
        """
        self.session_id = session_id
        self.client = None
        self.conversation_history = []
        self.initialized = False
        self.current_context = {}
        self.base_agent_text = ""  # Store the base agent's text/thinking

    async def initialize(self):
        """Initialize the Gemini client."""
        if not self.initialized:
            try:
                self.client = init_gemini()
                self.initialized = True
            except Exception as e:
                raise ValueError(f"Failed to initialize Gemini client: {str(e)}")

    async def _execute_mcp_call(self, function_call):
        """
        Execute a single MCP function call.

        Args:
            function_call: The function call to execute

        Returns:
            The result of the function call
        """
        try:
            from mcp_server import (
                log_step,
                mark_decision,
                log_tool_call,
                get_previous_steps,
                set_current_node,
                go_back_steps,
            )

            name = function_call.get("name")
            args = function_call.get("args", {})

            if not name:
                return {"error": "Invalid function call format: missing name"}

            result = None

            if name == "log_step":
                if "step_name" in args and "description" in args:
                    result = log_step(args["step_name"], args["description"])
                else:
                    return {"error": f"Missing required arguments for log_step: {args}"}

            elif name == "mark_decision":
                if all(
                    k in args
                    for k in ["decision_point", "options", "chosen_option", "reasoning"]
                ):
                    result = mark_decision(
                        args["decision_point"],
                        args["options"],
                        args["chosen_option"],
                        args["reasoning"],
                    )
                else:
                    return {
                        "error": f"Missing required arguments for mark_decision: {args}"
                    }

            elif name == "log_tool_call":
                if all(k in args for k in ["tool_name", "arguments", "result"]):
                    result = log_tool_call(
                        args["tool_name"], args["arguments"], args["result"]
                    )
                else:
                    return {
                        "error": f"Missing required arguments for log_tool_call: {args}"
                    }

            elif name == "get_previous_steps":
                num_steps = args.get("num_steps", 5)
                result = get_previous_steps(num_steps)

            elif name == "set_current_node":
                if "node_id" in args:
                    result = set_current_node(args["node_id"])
                else:
                    return {
                        "error": f"Missing required arguments for set_current_node: {args}"
                    }

            elif name == "go_back_steps":
                num_steps = args.get("num_steps", 1)
                result = go_back_steps(num_steps)

            else:
                return {"error": f"Unknown function call: {name}"}

            return {"success": True, "result": result}

        except Exception as e:
            return {
                "error": f"Error executing function call {function_call.get('name', 'unknown')}: {str(e)}"
            }

    async def analyze_base_agent_text(
        self, base_agent_text: str, system_prompt: str = None
    ):
        """
        Analyze text generated by the base agent to extract decision points, steps, and tool calls.

        Args:
            base_agent_text: Text generated by the base agent to analyze
            system_prompt: Optional custom system prompt to use

        Returns:
            Analysis results including extracted decision points, steps, and tool calls
        """
        await self.initialize()

        # Append the new text to the existing base agent text
        if self.base_agent_text:
            # Add a separator if there's existing text
            self.base_agent_text += "\n\n--- NEW TEXT ---\n\n"

        self.base_agent_text += base_agent_text

        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = """
            You are a meta-agent that analyzes the text and actions of another agent (the base agent).
            Your task is to extract decision points, options considered, chosen options, and reasoning.
            Also identify any steps or tool calls mentioned by the base agent.
            
            For each decision point, call the mark_decision function.
            For each step, call the log_step function.
            For each tool call, call the log_tool_call function.
            
            Make sure to preserve the hierarchical structure of the base agent's thinking process,
            so that parent-child relationships between nodes are maintained.
            
            Focus on analyzing NEW information that hasn't been processed before.
            Don't repeat function calls for content you've already analyzed.
            """

        # Create a message for the meta-agent to analyze
        meta_agent_message = {
            "role": "user",
            "content": f"Please analyze the following base agent text and extract decision points, steps, and tool calls:\n\n{base_agent_text}",
        }

        # Add the message to the conversation history
        self.conversation_history.append(meta_agent_message)

        # Create a Tool object with the function declarations
        tool = types.Tool(function_declarations=FUNCTION_DECLARATIONS)

        # Call Gemini with function calling
        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=self.conversation_history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                    max_output_tokens=4096,
                    tools=[tool],
                ),
            )

            # Process the response
            meta_agent_response = ""
            function_calls = []

            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        meta_agent_response += part.text

                    if (
                        hasattr(part, "function_call")
                        and part.function_call is not None
                    ):
                        try:
                            function_call = {
                                "name": part.function_call.name,
                                "args": part.function_call.args,
                            }
                            function_calls.append(function_call)

                            # Execute the function call
                            result = await self._execute_mcp_call(function_call)

                            # Add the function call and result to the conversation history
                            self.conversation_history.append(
                                {
                                    "role": "model",
                                    "content": f"Function call: {function_call['name']}",
                                    "function_call": function_call,
                                }
                            )

                            self.conversation_history.append(
                                {
                                    "role": "function",
                                    "name": function_call["name"],
                                    "content": json.dumps(result),
                                }
                            )

                        except AttributeError as attr_err:
                            print(
                                f"Warning: Malformed function call in response: {attr_err}"
                            )

            # Add the meta-agent's text response to the conversation history
            if meta_agent_response:
                self.conversation_history.append(
                    {"role": "model", "content": meta_agent_response}
                )

            return {"response": meta_agent_response, "function_calls": function_calls}

        except Exception as e:
            error_msg = f"Error processing with Gemini: {str(e)}"
            print(error_msg)
            return {"error": error_msg}

    async def meta_agent_query(self, query: str, system_prompt: str = None):
        """
        Query the meta-agent about the base agent's decision process.

        Args:
            query: The query to ask the meta-agent
            system_prompt: Optional custom system prompt to use

        Returns:
            The meta-agent's response
        """
        await self.initialize()

        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = """
            You are a meta-agent that analyzes and explains the decision process of another agent (the base agent).
            You have built a graph representation of the base agent's thinking and actions.
            
            You can use get_previous_steps to see what the base agent has done, and go_back_steps or set_current_node 
            to navigate to previous points in the base agent's decision process.
            
            When asked about the base agent's decisions or reasoning, use these navigation functions to explore
            the graph and provide insightful explanations about the base agent's thought process.
            
            Always think step by step and explain your reasoning clearly.
            """

        # Add the query to the conversation history
        self.conversation_history.append({"role": "user", "content": query})

        # Create a Tool object with the function declarations for navigation
        tool = types.Tool(function_declarations=NAVIGATION_FUNCTION_DECLARATIONS)

        # Call Gemini with function calling
        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=self.conversation_history,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                    max_output_tokens=4096,
                    tools=[tool],
                ),
            )

            # Process the response
            meta_agent_response = ""
            function_calls = []

            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        meta_agent_response += part.text

                    if (
                        hasattr(part, "function_call")
                        and part.function_call is not None
                    ):
                        try:
                            function_call = {
                                "name": part.function_call.name,
                                "args": part.function_call.args,
                            }
                            function_calls.append(function_call)

                            # Execute the function call
                            result = await self._execute_mcp_call(function_call)

                            # Add the function call and result to the conversation history
                            self.conversation_history.append(
                                {
                                    "role": "model",
                                    "content": f"Function call: {function_call['name']}",
                                    "function_call": function_call,
                                }
                            )

                            self.conversation_history.append(
                                {
                                    "role": "function",
                                    "name": function_call["name"],
                                    "content": json.dumps(result),
                                }
                            )

                        except AttributeError as attr_err:
                            print(
                                f"Warning: Malformed function call in response: {attr_err}"
                            )

            # Add the meta-agent's text response to the conversation history
            if meta_agent_response:
                self.conversation_history.append(
                    {"role": "model", "content": meta_agent_response}
                )

            return {"response": meta_agent_response, "function_calls": function_calls}

        except Exception as e:
            error_msg = f"Error processing with Gemini: {str(e)}"
            print(error_msg)
            return {"error": error_msg}

    async def explore_alternative_path(self, node_id: int, query: str = None):
        """
        Explore an alternative path by going back to a specific node and asking the meta-agent
        to analyze what might have happened if the base agent had made a different decision.

        Args:
            node_id: The ID of the node to go back to
            query: Optional query about the alternative path

        Returns:
            The result of setting the current node and the meta-agent's analysis
        """
        # Set the current node
        set_result = await self._execute_mcp_call(
            {"name": "set_current_node", "args": {"node_id": node_id}}
        )

        if set_result.get("error"):
            return set_result

        # Add a note to the conversation history about exploring an alternative path
        self.conversation_history.append(
            {
                "role": "system",
                "content": f"Exploring alternative path from node {node_id}.",
            }
        )

        # If a query is provided, ask the meta-agent about the alternative path
        if query:
            return await self.meta_agent_query(query)

        return {
            "success": True,
            "message": f"Set current node to {node_id}. Ready to explore alternative path.",
        }

    def reset(self):
        """Reset the meta-agent state."""
        self.conversation_history = []
        self.current_context = {}
        self.base_agent_text = ""

        # Create a new event loop for the reset operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Reset the trace in the MCP server by importing and calling a function
            # that will create a new trace next time it's needed
            import sys

            if "mcp_server" in sys.modules:
                # If mcp_server is already imported, reload it to reset the global variables
                import importlib

                importlib.reload(sys.modules["mcp_server"])

            # Alternatively, we could create a new trace explicitly
            try:
                from database import get_db
                from models import Trace

                db = next(get_db())
                trace = Trace(name="Agent Trace", description="New trace after reset")
                db.add(trace)
                db.commit()
            except Exception as e:
                print(f"Warning: Could not create a new trace: {str(e)}")
        finally:
            loop.close()
            asyncio.set_event_loop(None)


# Synchronous wrapper for the AgentLoopController
class SyncAgentLoopController:
    """
    A synchronous wrapper for the AgentLoopController class.
    """

    def __init__(self, session_id: str = "default_session"):
        """Initialize the synchronous meta-agent controller."""
        self.async_controller = AgentLoopController(session_id)
        # Initialize in a safe way that works both inside and outside event loops
        self._safe_initialize()

    def _safe_initialize(self):
        """Safely initialize the async controller without using asyncio.run()."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()

            # Check if we're in a running event loop
            if loop.is_running():
                # Create a new loop for initialization
                new_loop = asyncio.new_event_loop()
                try:
                    # Run the initialization in the new loop
                    new_loop.run_until_complete(self.async_controller.initialize())
                finally:
                    # Clean up the new loop
                    new_loop.close()
            else:
                # We can use the existing loop
                loop.run_until_complete(self.async_controller.initialize())
        except RuntimeError:
            # If we can't get an event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.async_controller.initialize())
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    def analyze_base_agent_text(self, base_agent_text: str, system_prompt: str = None):
        """
        Analyze text generated by the base agent to extract decision points, steps, and tool calls.

        Args:
            base_agent_text: Text generated by the base agent to analyze
            system_prompt: Optional custom system prompt to use

        Returns:
            Analysis results including extracted decision points, steps, and tool calls
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()

            # Check if we're in a running event loop
            if loop.is_running():
                # We're in a running event loop, create a new task
                # This is a workaround and might not work in all cases
                print(
                    "Warning: Running in an existing event loop. Results may be incomplete."
                )
                # Return empty results to avoid blocking
                return {
                    "error": "Cannot analyze base agent text in a running event loop."
                }
            else:
                # We can use the existing loop
                return loop.run_until_complete(
                    self.async_controller.analyze_base_agent_text(
                        base_agent_text, system_prompt
                    )
                )
        except RuntimeError:
            # If we can't get an event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.async_controller.analyze_base_agent_text(
                        base_agent_text, system_prompt
                    )
                )
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    def meta_agent_query(self, query: str, system_prompt: str = None):
        """
        Query the meta-agent about the base agent's decision process.

        Args:
            query: The query to ask the meta-agent
            system_prompt: Optional custom system prompt to use

        Returns:
            The meta-agent's response
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()

            # Check if we're in a running event loop
            if loop.is_running():
                # We're in a running event loop, create a new task
                # This is a workaround and might not work in all cases
                print(
                    "Warning: Running in an existing event loop. Results may be incomplete."
                )
                # Return empty results to avoid blocking
                return {"error": "Cannot query meta-agent in a running event loop."}
            else:
                # We can use the existing loop
                return loop.run_until_complete(
                    self.async_controller.meta_agent_query(query, system_prompt)
                )
        except RuntimeError:
            # If we can't get an event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.async_controller.meta_agent_query(query, system_prompt)
                )
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    def explore_alternative_path(self, node_id: int, query: str = None):
        """
        Explore an alternative path by going back to a specific node and asking the meta-agent
        to analyze what might have happened if the base agent had made a different decision.

        Args:
            node_id: The ID of the node to go back to
            query: Optional query about the alternative path

        Returns:
            The result of setting the current node and the meta-agent's analysis
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()

            # Check if we're in a running event loop
            if loop.is_running():
                # We're in a running event loop, create a new task
                # This is a workaround and might not work in all cases
                print(
                    "Warning: Running in an existing event loop. Results may be incomplete."
                )
                # Return empty results to avoid blocking
                return {
                    "error": "Cannot explore alternative path in a running event loop."
                }
            else:
                # We can use the existing loop
                return loop.run_until_complete(
                    self.async_controller.explore_alternative_path(node_id, query)
                )
        except RuntimeError:
            # If we can't get an event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.async_controller.explore_alternative_path(node_id, query)
                )
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    def reset(self):
        """Reset the meta-agent state."""
        self.async_controller.reset()
