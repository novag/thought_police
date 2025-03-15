#!/usr/bin/env python3
"""
Example script demonstrating how to use the AgentLoopController to build a graph
and navigate through previous decision points.
"""

from text_analyzer import SyncAgentLoopController


def main():
    """Run the agent example."""
    print("Starting Agent Loop Controller Example")
    print("======================================")

    # Create a new agent loop controller
    agent = SyncAgentLoopController(session_id="example_session")

    # Run the first agent step
    print(
        "\n[USER] Let's solve a complex problem: How should we approach building a recommendation system?"
    )
    result = agent.run_agent_step(
        "Let's solve a complex problem: How should we approach building a recommendation system?"
    )

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("\n[AGENT] " + result.get("response", ""))
    print("\nFunction calls made:", len(result.get("function_calls", [])))

    # Get the previous steps to see what decisions were made
    print("\n[USER] Show me the steps you've taken so far.")
    result = agent.run_agent_step("Show me the steps you've taken so far.")

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("\n[AGENT] " + result.get("response", ""))

    # Let's explore an alternative path
    print(
        "\n[USER] Let's explore a different approach. What if we used collaborative filtering instead?"
    )
    result = agent.run_agent_step(
        "Let's explore a different approach. What if we used collaborative filtering instead?"
    )

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("\n[AGENT] " + result.get("response", ""))

    # Get the previous steps again to see the new branch
    print(
        "\n[USER] Show me all the steps you've taken now, including the new approach."
    )
    result = agent.run_agent_step(
        "Show me all the steps you've taken now, including the new approach."
    )

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("\n[AGENT] " + result.get("response", ""))

    print("\n======================================")
    print("Example completed. Check the visualization to see the decision tree.")


async def async_main():
    """Run the agent example asynchronously."""
    from text_analyzer import AgentLoopController

    print("Starting Async Agent Loop Controller Example")
    print("===========================================")

    # Create a new agent loop controller
    agent = AgentLoopController(session_id="async_example_session")
    await agent.initialize()

    # Run the first agent step
    print(
        "\n[USER] Let's solve a complex problem: How should we approach building a recommendation system?"
    )
    result = await agent.run_agent_step(
        "Let's solve a complex problem: How should we approach building a recommendation system?"
    )

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("\n[AGENT] " + result.get("response", ""))
    print("\nFunction calls made:", len(result.get("function_calls", [])))

    # Get the previous steps to see what decisions were made
    print("\n[USER] Show me the steps you've taken so far.")
    result = await agent.run_agent_step("Show me the steps you've taken so far.")

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print("\n[AGENT] " + result.get("response", ""))

    # Let's explore an alternative path by going back to a specific node
    # First, we need to get the node ID of a decision point
    print(
        "\n[USER] Let's go back to your initial approach and explore a different path."
    )

    # Get previous steps to find a node ID to go back to
    get_steps_result = await agent._execute_mcp_call(
        {"name": "get_previous_steps", "args": {"num_steps": 10}}
    )

    if "error" in get_steps_result:
        print(f"Error getting previous steps: {get_steps_result['error']}")
        return

    # Find a decision node to go back to
    steps = get_steps_result.get("result", [])
    decision_node_id = None

    for step in steps:
        if step.get("type") == "decision":
            decision_node_id = step.get("id")
            break

    if decision_node_id:
        print(f"\nGoing back to decision node {decision_node_id}")

        # Explore an alternative path from this node
        result = await agent.explore_alternative_path(
            decision_node_id,
            "What if we used a hybrid approach combining content-based and collaborative filtering?",
        )

        if "error" in result:
            print(f"Error: {result['error']}")
            return

        print("\n[AGENT] " + result.get("response", ""))
    else:
        print("\nNo decision nodes found to go back to.")

    print("\n===========================================")
    print("Async example completed. Check the visualization to see the decision tree.")


if __name__ == "__main__":
    # Run the synchronous example by default
    main()

    # Uncomment to run the async example
    # asyncio.run(async_main())
