from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Operation


class ConflictResolver(ABC):
    @abstractmethod
    def resolve(self, local: Operation | None, incoming: Operation) -> Operation:
        ...


class LastWriteWinsResolver(ConflictResolver):
    def resolve(self, local: Operation | None, incoming: Operation) -> Operation:
        if local is None:
            return incoming
        if incoming.version > local.version:
            return incoming
        if incoming.version == local.version:
            return incoming if incoming.timestamp >= local.timestamp else local
        return local
