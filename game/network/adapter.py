"""Transport-agnostic network adapter contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class NetworkEvent:
    """A normalized inbound event for game-loop consumption."""

    event_type: str
    payload: dict[str, Any]
    event_id: str = ""


class NetworkAdapter(ABC):
    """Abstract network boundary for online gameplay flows."""

    @abstractmethod
    def connect(self) -> None:
        """Open transport connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close transport connection."""

    @abstractmethod
    def send(self, event_type: str, payload: dict[str, Any]) -> None:
        """Send one outbound event."""

    @abstractmethod
    def poll(self) -> list[NetworkEvent]:
        """Return newly received events since last poll."""


class NullNetworkAdapter(NetworkAdapter):
    """No-op adapter used until a real transport is implemented."""

    def connect(self) -> None:
        return None

    def disconnect(self) -> None:
        return None

    def send(self, event_type: str, payload: dict[str, Any]) -> None:
        return None

    def poll(self) -> list[NetworkEvent]:
        return []
