"""Unit tests for DAG validation and traversal."""

import pytest

from omniagent.control.engine.dag import (
    validate_dag,
    topological_sort,
    get_next_nodes,
    get_independent_nodes,
)
from omniagent.control.models.workflow import Edge, Node, NodeType, StateGraph
from omniagent.exceptions import ValidationError


def make_graph(nodes, edges, start, ends):
    return StateGraph(
        nodes=[Node(id=n, node_type=NodeType.TASK) for n in nodes],
        edges=[Edge(from_node=f, to_node=t) for f, t in edges],
        start_node=start,
        end_nodes=ends,
    )


@pytest.mark.unit
def test_valid_dag():
    graph = make_graph(["a", "b", "c"], [("a", "b"), ("b", "c")], "a", ["c"])
    validate_dag(graph)  # Should not raise


@pytest.mark.unit
def test_cycle_detection():
    graph = make_graph(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")], "a", ["c"])
    with pytest.raises(ValidationError, match="cycle"):
        validate_dag(graph)


@pytest.mark.unit
def test_missing_start_node():
    graph = make_graph(["a", "b"], [("a", "b")], "x", ["b"])
    with pytest.raises(ValidationError, match="Start node"):
        validate_dag(graph)


@pytest.mark.unit
def test_missing_end_node():
    graph = make_graph(["a", "b"], [("a", "b")], "a", ["x"])
    with pytest.raises(ValidationError, match="End node"):
        validate_dag(graph)


@pytest.mark.unit
def test_topological_sort():
    graph = make_graph(["a", "b", "c", "d"], [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")], "a", ["d"])
    order = topological_sort(graph)
    assert order[0] == "a"
    assert order[-1] == "d"


@pytest.mark.unit
def test_get_next_nodes():
    graph = make_graph(["a", "b", "c"], [("a", "b"), ("a", "c")], "a", ["b", "c"])
    nexts = get_next_nodes(graph, "a")
    assert set(nexts) == {"b", "c"}


@pytest.mark.unit
def test_get_independent_nodes():
    graph = make_graph(["a", "b", "c", "d"], [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")], "a", ["d"])
    levels = get_independent_nodes(graph)
    assert levels[0] == {"a"}
    assert levels[1] == {"b", "c"}
    assert levels[2] == {"d"}
