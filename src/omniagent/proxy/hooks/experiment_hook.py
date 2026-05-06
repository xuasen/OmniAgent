"""Pre-forward hook: route requests to experiment variants."""

import logging

from omniagent.intelligence.services.experiment_engine import ExperimentEngineService
from omniagent.proxy.hooks.base import HookContext

logger = logging.getLogger(__name__)


class ExperimentHook:
    def __init__(self, experiment_engine: ExperimentEngineService) -> None:
        self._experiment_engine = experiment_engine

    async def pre_forward(self, context: HookContext) -> HookContext:
        experiment_id = context.headers.get("x-omniagent-experiment")
        if not experiment_id:
            return context

        variant_id = self._experiment_engine.route_request(experiment_id)
        if variant_id:
            context.metadata["experiment_id"] = experiment_id
            context.metadata["variant_id"] = variant_id
            logger.debug(f"Request routed to experiment variant: {experiment_id}/{variant_id}")

        return context
