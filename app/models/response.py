from __future__ import annotations

from abc import ABCMeta, abstractmethod, ABC
from typing import Any


class APIResponse:
    __metaclass__ = ABCMeta

    @property
    def status(self) -> int:
        raise NotImplementedError

    @property
    def message(self) -> str:
        raise NotImplementedError

    @property
    def payload(self) -> dict:
        raise NotImplementedError

    def serialize(self) -> dict:
        return {
            "status": self.status,
            "message": self.message,
            "payload": self.payload
        }


class FilledResponse(APIResponse, ABC):

    def __init__(self, status: int = None, message: str = None, payload: dict = None):
        self._status: int = status
        self._message: str = message
        self._payload: Any = payload

    @property
    def status(self):
        return self._status

    @property
    def message(self):
        return self._message

    @property
    def payload(self):
        return self._payload


class AsyncResponse(FilledResponse, ABC):

    @abstractmethod
    async def complete(self) -> AsyncResponse:
        raise NotImplementedError


class SyncResponse(FilledResponse, ABC):

    @abstractmethod
    def complete(self) -> SyncResponse:
        raise NotImplementedError
