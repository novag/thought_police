from google import genai
from typing import List, Dict, Any


def init_gemini():
    """Initialize the Gemini API with the API key from environment variables."""
    return genai.Client(
        project="trail-ml-9e15e", location="us-central1", vertexai=True
    )  # Best pratice :)


class Node:
    """
    Represents a node in the chain documentation graph.
    Each node represents a step or decision point in the agent's control flow.
    """

    def __init__(self, content, id=None):
        """
        Initialize a node with content and optional ID.

        Args:
            content (str): The content/description of this node
            id (str, optional): Unique identifier for the node
        """
        self.content = content
        self.id = id
        self.children = []  # List of child nodes
        self.parent = None  # Reference to parent node

    def add_child(self, child_node):
        """
        Add a child node to this node.

        Args:
            child_node (Node): The node to add as a child
        """
        self.children.append(child_node)
        child_node.parent = self
        return child_node

    def __str__(self):
        """String representation of the node."""
        return f"Node({self.id}: {self.content})"


class ChainDocumenter:
    """
    Main class for documenting chains of actions/decisions.
    Creates and manages a graph representing the control flow.
    """

    def __init__(self):
        """Initialize the chain documenter with a root node."""
        self.root = Node("ROOT", id="root")
        self.current_node = self.root
        self.node_count = 0

    def create_node(self, content):
        """
        Create a new node and append it to the current node.

        Args:
            content (str): The content/description for the new node

        Returns:
            Node: The newly created node
        """
        self.node_count += 1
        node_id = f"node_{self.node_count}"
        new_node = Node(content, id=node_id)
        self.current_node.add_child(new_node)
        self.current_node = new_node
        return new_node

    def move_pointer(self, target_node):
        """
        Move the current pointer to another node in the graph.

        Args:
            target_node (Node): The node to move the pointer to

        Returns:
            Node: The node that is now current
        """
        self.current_node = target_node
        return self.current_node

    def view_last_n_nodes(self, n=5):
        """
        View the last n nodes along the current path.

        Args:
            n (int): Number of nodes to view

        Returns:
            list: List of the last n nodes
        """
        path = []
        current = self.current_node

        # Traverse up the tree to collect nodes
        while current and len(path) < n:
            path.insert(0, current)
            current = current.parent

        return path

    def get_full_path_to_current(self):
        """
        Get the full path from root to the current node.

        Returns:
            list: List of nodes from root to current
        """
        path = []
        current = self.current_node

        # Traverse up the tree to collect nodes
        while current:
            path.insert(0, current)
            current = current.parent

        return path

    def visualize_graph(self):
        """
        Generate a simple text visualization of the graph.

        Returns:
            str: Text representation of the graph
        """

        def _visualize_node(node, depth=0, is_last=False):
            # Prefix for the current node
            prefix = (
                "    " * (depth - 1) + ("└── " if is_last else "├── ")
                if depth > 0
                else ""
            )

            # Mark the current node
            current_marker = " [CURRENT]" if node == self.current_node else ""

            # Build the node representation
            result = [f"{prefix}{node.content}{current_marker}"]

            # Process children
            for i, child in enumerate(node.children):
                is_last_child = i == len(node.children) - 1
                result.extend(_visualize_node(child, depth + 1, is_last_child))

            return result

        # Start visualization from the root
        lines = _visualize_node(self.root)
        return "\n".join(lines)

    def analyze_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Analyze a block of text to determine what chain documentation actions to take.

        Args:
            text: The text to analyze

        Returns:
            A list of actions that were executed
        """
        # Split the text into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # Track all executed actions
        all_executed_actions = []

        # First pass: Create nodes for all steps before any branching
        print("\n=== First pass: Creating initial nodes ===")
        for i, paragraph in enumerate(paragraphs):
            # Stop at the first branching point
            if "BRANCH POINT:" in paragraph or "goes back to" in paragraph.lower():
                print(f"Stopping at paragraph {i+1} (branching point)")
                break

            print(f"\nProcessing paragraph {i+1}:")
            print(f"'{paragraph[:100]}{'...' if len(paragraph) > 100 else ''}'")

            # Create a node for this paragraph
            node = self.create_node(paragraph)
            all_executed_actions.append(
                {
                    "function": {"name": "create_node", "args": {"content": paragraph}},
                    "result": {
                        "success": True,
                        "result": {"node_id": node.id, "content": node.content},
                    },
                }
            )

            print("\nCurrent graph state:")
            print(self.visualize_graph())

        # Second pass: Process branching points
        print("\n=== Second pass: Processing branching points ===")
        branch_paragraphs = []
        for i, paragraph in enumerate(paragraphs):
            if "BRANCH POINT:" in paragraph or "goes back to" in paragraph.lower():
                branch_paragraphs.append((i, paragraph))

        for branch_idx, (para_idx, paragraph) in enumerate(branch_paragraphs):
            print(f"\nProcessing branch point {branch_idx+1}/{len(branch_paragraphs)}:")
            print(f"'{paragraph[:100]}{'...' if len(paragraph) > 100 else ''}'")

            # Extract the target node description from the paragraph
            target_desc = self._extract_target_description(paragraph)
            print(f"Target description: '{target_desc}'")

            # Find the best matching node
            target_node = self._find_best_matching_node(target_desc)
            if target_node:
                print(f"Found matching node: {target_node}")

                # Move pointer to the target node
                self.move_pointer(target_node)
                all_executed_actions.append(
                    {
                        "function": {
                            "name": "move_pointer_to_node",
                            "args": {"node_id": target_node.id},
                        },
                        "result": {
                            "success": True,
                            "result": {
                                "node_id": target_node.id,
                                "content": target_node.content,
                            },
                        },
                    }
                )

                # Process subsequent paragraphs until the next branch point
                next_branch_idx = para_idx + 1
                while next_branch_idx < len(paragraphs):
                    next_para = paragraphs[next_branch_idx]
                    if (
                        "BRANCH POINT:" in next_para
                        or "goes back to" in next_para.lower()
                    ):
                        break

                    print(f"\nProcessing paragraph after branch {next_branch_idx+1}:")
                    print(f"'{next_para[:100]}{'...' if len(next_para) > 100 else ''}'")

                    # Create a node for this paragraph
                    node = self.create_node(next_para)
                    all_executed_actions.append(
                        {
                            "function": {
                                "name": "create_node",
                                "args": {"content": next_para},
                            },
                            "result": {
                                "success": True,
                                "result": {"node_id": node.id, "content": node.content},
                            },
                        }
                    )

                    next_branch_idx += 1

                print("\nCurrent graph state:")
                print(self.visualize_graph())
            else:
                print(f"Could not find a matching node for '{target_desc}'")

        return all_executed_actions

    def _extract_target_description(self, paragraph: str) -> str:
        """
        Extract the description of the target node from a branching paragraph.

        Args:
            paragraph: The paragraph containing the branching point

        Returns:
            The description of the target node
        """
        # Check for explicit target in parentheses
        if "(" in paragraph and ")" in paragraph:
            start = paragraph.find("(")
            end = paragraph.find(")", start)
            if start != -1 and end != -1:
                return paragraph[start + 1 : end].strip()

        # Look for common phrases
        phrases = [
            "goes back to",
            "returns to",
            "revisits",
            "reconsiders",
            "go back to",
        ]

        for phrase in phrases:
            if phrase in paragraph.lower():
                # Extract the text after the phrase
                start = paragraph.lower().find(phrase) + len(phrase)
                # Find the end of the target description (usually ends with a period or "and")
                end = paragraph.find(".", start)
                if end == -1:
                    end = paragraph.find(" and ", start)
                if end == -1:
                    end = len(paragraph)

                return paragraph[start:end].strip()

        # Default to a generic description if no specific target is found
        return "research phase"

    def _find_best_matching_node(self, target_desc: str) -> Node:
        """
        Find the node that best matches the target description.

        Args:
            target_desc: The description of the target node

        Returns:
            The best matching node, or None if no match is found
        """
        # Get all nodes in the graph
        all_nodes = self._get_all_nodes()

        # If the target description is very specific, look for an exact match
        for node in all_nodes:
            if target_desc.lower() in node.content.lower():
                return node

        # Look for keywords in the target description
        keywords = [
            "research",
            "paper",
            "approach",
            "implement",
            "prototype",
            "analyze",
            "problem",
            "solution",
            "test",
            "optimize",
        ]

        best_match = None
        best_score = 0

        for node in all_nodes:
            score = 0
            for keyword in keywords:
                if keyword in target_desc.lower() and keyword in node.content.lower():
                    score += 1

            if score > best_score:
                best_score = score
                best_match = node

        # If we found a match with at least one keyword, return it
        if best_score > 0:
            return best_match

        # If all else fails, return the node that's 3 steps back from the current node
        # (this is a heuristic based on common branching patterns)
        path = self.get_full_path_to_current()
        if len(path) >= 4:  # root + at least 3 nodes
            return path[-4]  # 3 steps back from current

        # If the path is too short, return the earliest non-root node
        if len(path) >= 2:  # root + at least 1 node
            return path[1]  # First non-root node

        # Last resort: return the root
        return self.root

    def _get_all_nodes(self) -> List[Node]:
        """
        Get all nodes in the graph using breadth-first search.

        Returns:
            A list of all nodes in the graph
        """
        all_nodes = []
        queue = [self.root]

        while queue:
            current = queue.pop(0)
            all_nodes.append(current)
            queue.extend(current.children)

        return all_nodes


def parse_text_to_chain(text: str) -> ChainDocumenter:
    """
    Parse a block of text to generate a chain documentation graph.

    Args:
        text: The text to parse

    Returns:
        ChainDocumenter: The generated chain documenter with the graph
    """
    documenter = ChainDocumenter()

    # Use the analyze_text method to process the text
    actions = documenter.analyze_text(text)

    # Log the actions that were taken
    print(f"Executed {len(actions)} actions based on text analysis:")
    for i, action in enumerate(actions):
        function_name = action["function"]["name"]
        args = action["function"]["args"]
        result = action["result"]
        print(f"{i+1}. {function_name}({args}) -> {result}")

    return documenter


def test_branching_visualization():
    """
    Create a test graph with branches to verify visualization works correctly.
    """
    documenter = ChainDocumenter()

    # Create main branch
    node1 = documenter.create_node("Step 1: Analyze problem")
    node2 = documenter.create_node("Step 2: Research solutions")
    node3 = documenter.create_node("Step 3: Find papers")
    node4 = documenter.create_node("Step 4: Read paper A")
    node5 = documenter.create_node("Step 5: Implement approach A")

    # Move back to node3 and create a branch
    documenter.move_pointer(node3)
    branch1_node1 = documenter.create_node("Step 4B: Read paper B")
    branch1_node2 = documenter.create_node("Step 5B: Implement approach B")

    # Move back to node5 and create another branch
    documenter.move_pointer(node5)
    branch2_node1 = documenter.create_node("Step 6A: Optimize approach A")

    # Move back to branch1_node2 and continue that branch
    documenter.move_pointer(branch1_node2)
    branch1_node3 = documenter.create_node("Step 6B: Finalize approach B")

    print("\nManually created branching graph visualization:")
    print(documenter.visualize_graph())

    return documenter


# Example usage
if __name__ == "__main__":
    # First test our visualization with a manually created branching graph
    test_branching_visualization()

    # Then try with Gemini
    example_text = """
    The agent begins by analyzing the problem in detail.
    After analyzing the problem, the agent identifies several possible approaches.
    The agent decides to first research existing solutions to similar problems.
    The agent finds three relevant papers that describe different approaches.
    The agent reads the first paper and extracts key insights about approach A.
    The agent implements a prototype based on approach A and tests it.
    The prototype shows promising results but has some limitations.
    
    BRANCH POINT: The agent decides to go back to the research phase (where it found three papers) and examine the second paper instead.
    The second paper describes approach B, which seems more suitable for the current problem.
    The agent implements a prototype based on approach B and tests it.
    The approach B prototype performs significantly better than the approach A prototype.
    
    BRANCH POINT: The agent then decides to revisit the implementation of approach A (the step where it implemented the approach A prototype) to see if it can be improved.
    After making several optimizations to approach A, the agent tests it again.
    The improved approach A now performs almost as well as approach B but is simpler to implement.
    
    BRANCH POINT: The agent finally decides to create a hybrid solution that combines the best elements of both approaches.
    The hybrid approach performs even better than either approach alone.
    The agent finalizes the implementation and documents the solution.
    """

    print("\n\n" + "=" * 80)
    print("Now testing with Gemini analysis:")
    chain = parse_text_to_chain(example_text)

    print("\nGemini-created graph visualization:")
    print(chain.visualize_graph())
