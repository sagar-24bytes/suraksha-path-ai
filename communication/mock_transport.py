"""
SurakshaPath AI — In-Memory Mock Transport Implementation.

Provides a thread-safe, in-memory pub/sub message broker used for local simulation,
firmware unit testing, and dashboard operation before physical MQTT hardware exists.

Features:
  - Thread-safe callback registration and message dispatching
  - Multi-publisher and multi-subscriber support
  - Exact and wildcard prefix topic matching (e.g. "suraksha/telemetry/#")
  - Transmission statistics and packet audit log for testing
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional, Set

from communication.interface import CommunicationInterface, PacketCallback
from communication.packet_schema import TelemetryPacket

logger = logging.getLogger(__name__)


class MockTransport(CommunicationInterface):
    """In-memory pub/sub transport implementing CommunicationInterface."""

    def __init__(self, name: str = "MockTransport") -> None:
        """Initialize MockTransport.

        Args:
            name: Identifier name for logging/debugging.
        """
        self.name = name
        self._connected: bool = False
        self._lock: threading.RLock = threading.RLock()
        
        # Subscriptions: topic -> Set[PacketCallback]
        self._subscriptions: Dict[str, Set[PacketCallback]] = {}
        
        # Audit statistics for verification
        self._published_count: int = 0
        self._delivered_count: int = 0
        self._history: List[tuple[str, TelemetryPacket]] = []

    def connect(self) -> bool:
        """Establish in-memory transport connection."""
        with self._lock:
            self._connected = True
            logger.info("[%s] Connected successfully.", self.name)
            return True

    def disconnect(self) -> bool:
        """Close in-memory transport connection."""
        with self._lock:
            self._connected = False
            logger.info("[%s] Disconnected.", self.name)
            return True

    @property
    def is_connected(self) -> bool:
        """Check connection state."""
        with self._lock:
            return self._connected

    def publish(self, topic: str, packet: TelemetryPacket) -> bool:
        """Publish a packet to a topic and dispatch to subscribers.

        Args:
            topic: Destination topic string.
            packet: Canonical TelemetryPacket to publish.

        Returns:
            True if transport is connected and packet was processed, False otherwise.
        """
        with self._lock:
            if not self._connected:
                logger.warning("[%s] Publish failed: Transport not connected.", self.name)
                return False

            if not packet.validate():
                logger.warning("[%s] Publish failed: Packet validation failed for node %s.", self.name, packet.node_id)
                return False

            self._published_count += 1
            self._history.append((topic, packet))

            # Match subscribers (exact topic or wildcard prefix matching)
            target_callbacks: Set[PacketCallback] = set()
            for sub_topic, callbacks in self._subscriptions.items():
                if self._topic_matches(sub_topic, topic):
                    target_callbacks.update(callbacks)

            # Dispatch callbacks
            for callback in target_callbacks:
                try:
                    callback(topic, packet)
                    self._delivered_count += 1
                except Exception as e:
                    logger.error("[%s] Callback error on topic '%s': %s", self.name, topic, e, exc_info=True)

            return True

    def subscribe(self, topic: str, callback: PacketCallback) -> bool:
        """Register a callback for a topic.

        Args:
            topic: Topic string or pattern (e.g., "suraksha/telemetry/R-105" or "suraksha/telemetry/#").
            callback: Function to invoke when a matching packet arrives.

        Returns:
            True if subscription was registered, False if transport disconnected.
        """
        with self._lock:
            if not self._connected:
                logger.warning("[%s] Subscribe failed: Transport not connected.", self.name)
                return False

            if topic not in self._subscriptions:
                self._subscriptions[topic] = set()
            
            self._subscriptions[topic].add(callback)
            logger.debug("[%s] Subscribed callback to '%s'", self.name, topic)
            return True

    def unsubscribe(self, topic: str, callback: Optional[PacketCallback] = None) -> bool:
        """Remove callback(s) from a topic.

        Args:
            topic: Topic string.
            callback: Specific callback to remove, or None to remove all.

        Returns:
            True if unsubscription was performed, False otherwise.
        """
        with self._lock:
            if topic not in self._subscriptions:
                return False

            if callback is None:
                del self._subscriptions[topic]
            else:
                self._subscriptions[topic].discard(callback)
                if not self._subscriptions[topic]:
                    del self._subscriptions[topic]
            
            logger.debug("[%s] Unsubscribed from '%s'", self.name, topic)
            return True

    def get_stats(self) -> Dict[str, int]:
        """Return diagnostic counters for testing.

        Returns:
            Dictionary with published_count, delivered_count, active_topics.
        """
        with self._lock:
            return {
                "published_count": self._published_count,
                "delivered_count": self._delivered_count,
                "active_topics": len(self._subscriptions),
                "history_length": len(self._history),
            }

    def clear_history(self) -> None:
        """Clear published history for testing."""
        with self._lock:
            self._history.clear()
            self._published_count = 0
            self._delivered_count = 0

    @staticmethod
    def _topic_matches(subscription: str, topic: str) -> bool:
        """Check if a published topic matches a subscription pattern.

        Supports:
          - Exact match ("a/b/c" == "a/b/c")
          - Multi-level wildcard '#' ("a/b/#" matches "a/b/c", "a/b/c/d")
          - Single-level wildcard '+' ("a/+/c" matches "a/b/c")
        """
        if subscription == topic or subscription == "#":
            return True

        sub_parts = subscription.split("/")
        top_parts = topic.split("/")

        for i, sub_part in enumerate(sub_parts):
            if sub_part == "#":
                return True
            if i >= len(top_parts):
                return False
            if sub_part != "+" and sub_part != top_parts[i]:
                return False

        return len(sub_parts) == len(top_parts)
