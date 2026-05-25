"""Networking scaffolding package for online PvP."""

from game.network.adapter import NetworkAdapter, NetworkEvent, NullNetworkAdapter
from game.network.bootstrap import create_online_adapter
from game.network.online_sync import (
	apply_authoritative_clock,
	apply_authoritative_move,
	apply_authoritative_state,
	build_move_intent_payload,
)
from game.network.protocol_contract import PROTOCOL_VERSION, validate_envelope
from game.network.session_manager import SessionManager
from game.network.tcp_adapter import TcpJsonNetworkAdapter
from game.network.transport_shim import SessionManagerClientAdapter, SessionManagerHub

__all__ = [
	"NetworkAdapter",
	"NetworkEvent",
	"NullNetworkAdapter",
	"PROTOCOL_VERSION",
	"create_online_adapter",
	"apply_authoritative_clock",
	"apply_authoritative_move",
	"apply_authoritative_state",
	"build_move_intent_payload",
	"SessionManagerClientAdapter",
	"SessionManagerHub",
	"SessionManager",
	"TcpJsonNetworkAdapter",
	"validate_envelope",
]
