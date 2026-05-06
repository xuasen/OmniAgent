"""Base service protocol and implementation."""

import logging
from typing import Protocol, runtime_checkable


@runtime_checkable
class ServiceProtocol(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def health_check(self) -> bool: ...


class BaseService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self._started = False

    async def start(self) -> None:
        self._started = True
        self.logger.info(f"{self.__class__.__name__} started")

    async def stop(self) -> None:
        self._started = False
        self.logger.info(f"{self.__class__.__name__} stopped")

    async def health_check(self) -> bool:
        return self._started
