"""Unit tests for WorkflowParserService."""

import pytest

from omniagent.control.services.workflow_parser import WorkflowParserService
from omniagent.exceptions import ValidationError


@pytest.fixture
def parser():
    return WorkflowParserService(schema_path=None)


VALID_YAML = """
name: test-workflow
version: "1.0"
description: Test
graph:
  nodes:
    - id: start
      node_type: task
      action: init
    - id: end
      node_type: task
      action: finish
  edges:
    - from_node: start
      to_node: end
  start_node: start
  end_nodes:
    - end
"""


@pytest.mark.unit
def test_parse_valid_yaml(parser):
    wf = parser.parse_yaml(VALID_YAML)
    assert wf.name == "test-workflow"
    assert wf.version == "1.0"
    assert len(wf.graph.nodes) == 2
    assert wf.graph.start_node == "start"


@pytest.mark.unit
def test_round_trip(parser):
    wf = parser.parse_yaml(VALID_YAML)
    result = parser.round_trip(wf)
    assert result.name == wf.name
    assert result.graph.start_node == wf.graph.start_node
    assert len(result.graph.nodes) == len(wf.graph.nodes)


@pytest.mark.unit
def test_invalid_yaml_syntax(parser):
    with pytest.raises(ValidationError, match="YAML syntax error"):
        parser.parse_yaml("  invalid:\n    - [unclosed")


@pytest.mark.unit
def test_to_yaml(parser):
    wf = parser.parse_yaml(VALID_YAML)
    yaml_str = parser.to_yaml(wf)
    assert "test-workflow" in yaml_str
    assert "start_node" in yaml_str
