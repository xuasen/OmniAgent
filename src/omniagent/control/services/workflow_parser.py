"""Workflow definition parser — YAML parsing and schema validation (Req 10)."""

import json
import logging
from pathlib import Path

import yaml
import jsonschema

from omniagent.common.base_service import BaseService
from omniagent.control.models.workflow import WorkflowDefinition, StateGraph
from omniagent.exceptions import ValidationError

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path("schemas/workflow.schema.json")


class WorkflowParserService(BaseService):
    def __init__(self, schema_path: Path | None = None) -> None:
        super().__init__()
        self._schema_path = schema_path or SCHEMA_PATH
        self._schema: dict | None = None

    async def start(self) -> None:
        await super().start()
        if self._schema_path.exists():
            with open(self._schema_path) as f:
                self._schema = json.load(f)

    def parse_yaml(self, yaml_content: str) -> WorkflowDefinition:
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            mark = getattr(e, "problem_mark", None)
            if mark:
                raise ValidationError(
                    f"YAML syntax error at line {mark.line + 1}, column {mark.column + 1}",
                    details={"line": mark.line + 1, "column": mark.column + 1},
                )
            raise ValidationError(f"YAML syntax error: {e}")

        if self._schema:
            self._validate_schema(data)

        return WorkflowDefinition.model_validate(data)

    def to_yaml(self, workflow: WorkflowDefinition) -> str:
        data = workflow.model_dump(mode="json")
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def round_trip(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        yaml_str = self.to_yaml(workflow)
        return self.parse_yaml(yaml_str)

    def _validate_schema(self, data: dict) -> None:
        if not self._schema:
            return
        validator = jsonschema.Draft7Validator(self._schema)
        errors = list(validator.iter_errors(data))
        if errors:
            violations = []
            for error in errors:
                path = ".".join(str(p) for p in error.path) or "(root)"
                violations.append({"path": path, "message": error.message})
            raise ValidationError(
                "Workflow definition does not conform to schema",
                details={"violations": violations},
            )
