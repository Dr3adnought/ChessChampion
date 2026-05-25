"""Networking scaffolding package for online PvP."""

from game.network.adapter import NetworkAdapter, NetworkEvent, NullNetworkAdapter
from game.network.protocol_contract import PROTOCOL_VERSION, validate_envelope
from game.network.session_manager import SessionManager
from game.network.transport_shim import SessionManagerClientAdapter, SessionManagerHub

__all__ = [
	"NetworkAdapter",
	"NetworkEvent",
	"NullNetworkAdapter",
	"PROTOCOL_VERSION",
	"SessionManagerClientAdapter",
	"SessionManagerHub",
	"SessionManager",
	"validate_envelope",
]
