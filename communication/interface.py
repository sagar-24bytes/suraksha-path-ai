"""
SurakshaPath AI — Communication Interface Abstraction.

Defines the abstract base class `CommunicationInterface` that all transport
implementations (MockTransport, MQTTTransport, etc.) must implement.

No business logic inside Simulation, MicroPython Firmware, or the Fire Commander
Dashboard depends on a specific transport implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Optional

from communication.packet_schema import TelemetryPacket


# Type alias for topic callback functions: callback(topic: str, packet: TelemetryPacket)
PacketCallback = Callable[[str, TelemetryPacket], None]


class CommunicationInterface(ABC):
    """Abstract Base Class for transport implementations."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection with the transport broker/medium.

        Returns:
            True if connection was successful, False otherwise.
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close connection with the transport broker/medium.

        Returns:
            True if disconnection was successful, False otherwise.
        """
        pass

    @abstractmethod
    def publish(self, topic: str, packet: TelemetryPacket) -> bool:
        """Publish a TelemetryPacket to a specified topic.

        Args:
            topic: Destination topic string (e.g., "suraksha/telemetry/R-105").
            packet: Canonical TelemetryPacket to transmit.

        Returns:
            True if packet was published successfully, False otherwise.
        """
        pass

    @abstractmethod
    def subscribe(self, topic: str, callback: PacketCallback) -> bool:
        """Subscribe a callback to receive packets from a topic.

        Args:
            topic: Topic string or pattern to subscribe to.
            callback: Function to invoke when a packet is received on the topic.

        Returns:
            True if subscription was registered successfully, False otherwise.
        """
        pass

    @abstractmethod
    def unsubscribe(self, topic: str, callback: Optional[PacketCallback] = None) -> bool:
        """Unsubscribe a callback from a topic.

        Args:
            topic: Topic string to unsubscribe from.
            callback: Specific callback to remove, or None to remove all.

        Returns:
            True if unsubscription was successful, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection state.

        Returns:
            True if transport is connected, False otherwise.
        """
        pass
