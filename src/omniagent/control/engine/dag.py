"""DAG validation and traversal (Req 5)."""

from collections import defaultdict, deque

from omniagent.control.models.workflow import StateGraph, Node
from omniagent.exceptions import ValidationError


def validate_dag(graph: StateGraph) -> None:
    node_ids = {n.id for n in graph.nodes}

    if graph.start_node not in node_ids:
        raise ValidationError(
            f"Start node '{graph.start_node}' not found in graph nodes",
            details={"start_node": graph.start_node},
        )

    for end_node in graph.end_nodes:
        if end_node not in node_ids:
            raise ValidationError(
                f"End node '{end_node}' not found in graph nodes",
                details={"end_node": end_node},
            )

    for edge in graph.edges:
        if edge.from_node not in node_ids:
            raise ValidationError(f"Edge references unknown node: {edge.from_node}")
        if edge.to_node not in node_ids:
            raise ValidationError(f"Edge references unknown node: {edge.to_node}")

    if _has_cycle(graph):
        raise ValidationError("State graph contains a cycle")


def _has_cycle(graph: StateGraph) -> bool:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in graph.edges:
        adjacency[edge.from_node].append(edge.to_node)

    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(node: str) -> bool:
        visited.add(node)
        in_stack.add(node)
        for neighbor in adjacency[node]:
            if neighbor in in_stack:
                return True
            if neighbor not in visited and dfs(neighbor):
                return True
        in_stack.discard(node)
        return False

    for node in graph.nodes:
        if node.id not in visited:
            if dfs(node.id):
                return True
    return False


def topological_sort(graph: StateGraph) -> list[str]:
    in_degree: dict[str, int] = {n.id: 0 for n in graph.nodes}
    adjacency: dict[str, list[str]] = defaultdict(list)

    for edge in graph.edges:
        adjacency[edge.from_node].append(edge.to_node)
        in_degree[edge.to_node] += 1

    queue = deque([n for n, deg in in_degree.items() if deg == 0])
    order: list[str] = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in adjacency[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return order


def get_next_nodes(graph: StateGraph, current_node: str) -> list[str]:
    return [e.to_node for e in graph.edges if e.from_node == current_node]


def get_predecessors(graph: StateGraph, node_id: str) -> list[str]:
    return [e.from_node for e in graph.edges if e.to_node == node_id]


def get_independent_nodes(graph: StateGraph) -> list[set[str]]:
    """Find groups of nodes that can execute in parallel (no dependency edges between them)."""
    in_degree: dict[str, int] = {n.id: 0 for n in graph.nodes}
    adjacency: dict[str, list[str]] = defaultdict(list)

    for edge in graph.edges:
        adjacency[edge.from_node].append(edge.to_node)
        in_degree[edge.to_node] += 1

    levels: list[set[str]] = []
    queue = deque([n for n, deg in in_degree.items() if deg == 0])

    while queue:
        level = set(queue)
        levels.append(level)
        next_queue: deque[str] = deque()
        for node in queue:
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        queue = next_queue

    return levels
