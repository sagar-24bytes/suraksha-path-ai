"""
SurakshaPath AI — Communication Layer Package.

Transport abstraction layer decoupling Simulation, MicroPython Firmware, and Dashboard.

Exports:
  - TelemetryPacket: Canonical shared packet schema
  - CommunicationInterface: Abstract Base Class for transport abstractions
  - MockTransport: In-memory pub/sub queue transport for simulation and testing
  - MQTTTransport: Architecture-ready MQTT transport implementation
"""

from communication.packet_schema import TelemetryPacket
from communication.interface import CommunicationInterface, PacketCallback
from communication.mock_transport import MockTransport
from communication.mqtt_transport import MQTTTransport

__all__ = [
    "TelemetryPacket",
    "CommunicationInterface",
    "PacketCallback",
    "MockTransport",
    "MQTTTransport",
]
