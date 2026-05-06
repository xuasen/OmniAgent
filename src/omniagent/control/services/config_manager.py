"""Configuration manager — hot-reload support (Req 9)."""

import logging
import signal
from pathlib import Path

from omniagent.common.base_service import BaseService
from omniagent.common.config_loader import load_yaml_config
from omniagent.common.events import Event, EventBus

logger = logging.getLogger(__name__)


class ConfigManagerService(BaseService):
    def __init__(self, config_path: str, event_bus: EventBus) -> None:
        super().__init__()
        self._config_path = Path(config_path)
        self._event_bus = event_bus
        self._current_config: dict = {}

    async def start(self) -> None:
        await super().start()
        self._current_config = self._load()
        signal.signal(signal.SIGHUP, self._handle_reload_signal)
        logger.info(f"Config manager started, watching: {self._config_path}")

    async def stop(self) -> None:
        await super().stop()
        signal.signal(signal.SIGHUP, signal.SIG_DFL)

    async def reload(self) -> dict:
        new_config = self._load()
        changed_keys = self._diff(self._current_config, new_config)
        self._current_config = new_config

        if changed_keys:
            await self._event_bus.publish(Event(
                event_type="config.reloaded",
                payload={"changed_keys": changed_keys},
                source="config_manager",
            ))
            logger.info(f"Config reloaded, changed keys: {changed_keys}")

        return new_config

    @property
    def current_config(self) -> dict:
        return self._current_config

    def _load(self) -> dict:
        if not self._config_path.exists():
            logger.warning(f"Config file not found: {self._config_path}")
            return {}
        return load_yaml_config(self._config_path)

    def _handle_reload_signal(self, signum: int, frame: object) -> None:
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(self.reload())

    def _diff(self, old: dict, new: dict) -> list[str]:
        changed = []
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            if old.get(key) != new.get(key):
                changed.append(key)
        return changed
