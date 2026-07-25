"""
SurakshaPath AI — Architecture-Ready MQTT Transport Implementation.

Implements `CommunicationInterface` using standard MQTT protocol patterns.
Designed so that switching to a physical MQTT broker requires zero changes to the rest of the application.

Features:
  - Graceful fallback when `paho-mqtt` is not installed or broker is unavailable
  - Same pub/sub interface as MockTransport
  - Pre-configured topic structure (`suraksha/{building_id}/telemetry/{node_id}`)
  - Architecture-ready for physical ESP32 hardware and Node-RED integration
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, Optional, Set

from communication.interface import CommunicationInterface, PacketCallback
from communication.packet_schema import TelemetryPacket

logger = logging.getLogger(__name__)

# Lazy import check for paho-mqtt
try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    PAHO_AVAILABLE = False
    mqtt = None


class MQTTTransport(CommunicationInterface):
    """MQTT transport implementation of CommunicationInterface."""

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "suraksha_commander",
        keepalive: int = 60,
    ) -> None:
        """Initialize MQTTTransport.

        Args:
            broker_host: MQTT broker hostname or IP address.
            broker_port: MQTT broker port (default 1883).
            client_id: Unique client identifier for MQTT.
            keepalive: Keepalive timeout in seconds.
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.keepalive = keepalive

        self._connected: bool = False
        self._lock: threading.RLock = threading.RLock()
        self._subscriptions: Dict[str, Set[PacketCallback]] = {}
        self._client: Optional[Any] = None

    def connect(self) -> bool:
        """Connect to the MQTT broker.

        If `paho-mqtt` is not installed or broker connection fails, logs a clear warning
        and gracefully sets connected state according to fallback rules without crashing.
        """
        with self._lock:
            if not PAHO_AVAILABLE:
                logger.warning(
                    "[MQTTTransport] 'paho-mqtt' package not installed. "
                    "Operating in architectural standby mode. Install via 'pip install paho-mqtt'."
                )
                self._connected = False
                return False

            try:
                self._client = mqtt.Client(client_id=self.client_id)
                self._client.on_connect = self._on_mqtt_connect
                self._client.on_message = self._on_mqtt_message
                self._client.connect(self.broker_host, self.broker_port, self.keepalive)
                self._client.loop_start()
                self._connected = True
                logger.info("[MQTTTransport] Connected to broker at %s:%d", self.broker_host, self.broker_port)
                return True
            except Exception as e:
                logger.warning("[MQTTTransport] Broker connection to %s:%d failed: %s", self.broker_host, self.broker_port, e)
                self._connected = False
                return False

    def disconnect(self) -> bool:
        """Disconnect from the MQTT broker."""
        with self._lock:
            if self._client is not None:
                try:
                    self._client.loop_stop()
                    self._client.disconnect()
                except Exception as e:
                    logger.error("[MQTTTransport] Disconnect error: %s", e)
                finally:
                    self._client = None
            
            self._connected = False
            logger.info("[MQTTTransport] Disconnected.")
            return True

    @property
    def is_connected(self) -> bool:
        """Check connection state."""
        with self._lock:
            return self._connected

    def publish(self, topic: str, packet: TelemetryPacket) -> bool:
        """Publish a TelemetryPacket over MQTT.

        Args:
            topic: MQTT topic (e.g., "suraksha/telemetry/R-105").
            packet: Canonical TelemetryPacket to serialize and publish.

        Returns:
            True if published successfully, False otherwise.
        """
        with self._lock:
            if not packet.validate():
                logger.warning("[MQTTTransport] Publish rejected: Invalid packet.")
                return False

            payload = packet.to_json()

            if not self._connected or self._client is None:
                logger.debug("[MQTTTransport Standby] Would publish to '%s': %s", topic, payload[:80])
                return False

            try:
                info = self._client.publish(topic, payload, qos=1)
                return info.rc == mqtt.MQTT_ERR_SUCCESS
            except Exception as e:
                logger.error("[MQTTTransport] Publish error on topic '%s': %s", topic, e)
                return False

    def subscribe(self, topic: str, callback: PacketCallback) -> bool:
        """Subscribe to an MQTT topic with a callback.

        Args:
            topic: MQTT topic pattern.
            callback: PacketCallback to invoke on incoming message.

        Returns:
            True if registered.
        """
        with self._lock:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = set()
            self._subscriptions[topic].add(callback)

            if self._connected and self._client is not None:
                try:
                    self._client.subscribe(topic, qos=1)
                except Exception as e:
                    logger.error("[MQTTTransport] MQTT subscribe error for '%s': %s", topic, e)

            return True

    def unsubscribe(self, topic: str, callback: Optional[PacketCallback] = None) -> bool:
        """Unsubscribe from an MQTT topic."""
        with self._lock:
            if topic not in self._subscriptions:
                return False

            if callback is None:
                del self._subscriptions[topic]
            else:
                self._subscriptions[topic].discard(callback)
                if not self._subscriptions[topic]:
                    del self._subscriptions[topic]

            if self._connected and self._client is not None and topic not in self._subscriptions:
                try:
                    self._client.unsubscribe(topic)
                except Exception as e:
                    logger.error("[MQTTTransport] MQTT unsubscribe error for '%s': %s", topic, e)

            return True

    def _on_mqtt_connect(self, client: Any, userdata: Any, flags: Any, rc: int) -> None:
        """Internal callback when Paho MQTT connects to broker."""
        if rc == 0:
            logger.info("[MQTTTransport] MQTT broker session established.")
            # Resubscribe all active topics
            for topic in self._subscriptions:
                client.subscribe(topic, qos=1)
        else:
            logger.warning("[MQTTTransport] Broker connection refused with code %d", rc)

    def _on_mqtt_message(self, client: Any, userdata: Any, msg: Any) -> None:
        """Internal callback when Paho MQTT receives a message."""
        topic = msg.topic
        try:
            payload_str = msg.payload.decode("utf-8")
            packet = TelemetryPacket.from_json(payload_str)
            
            with self._lock:
                callbacks: Set[PacketCallback] = set()
                for sub_topic, sub_callbacks in self._subscriptions.items():
                    if MockTransport._topic_matches(sub_topic, topic):
                        callbacks.update(sub_callbacks)

            for cb in callbacks:
                try:
                    cb(topic, packet)
                except Exception as e:
                    logger.error("[MQTTTransport] Callback error on '%s': %s", topic, e)
        except Exception as e:
            logger.error("[MQTTTransport] Failed to parse incoming packet on '%s': %s", topic, e)
