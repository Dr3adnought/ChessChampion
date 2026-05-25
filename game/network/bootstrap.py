"""Adapter bootstrap helpers for selecting online transport backends."""

from __future__ import annotations

import os
from typing import Optional

from game.network.adapter import NetworkAdapter
from game.network.tcp_adapter import TcpJsonNetworkAdapter
from game.network.transport_shim import SessionManagerClientAdapter, SessionManagerHub

DEFAULT_TRANSPORT = "shim"
DEFAULT_TCP_HOST = "127.0.0.1"
DEFAULT_TCP_PORT = 8765


def create_online_adapter(
    *,
    transport: Optional[str] = None,
    hub: Optional[SessionManagerHub] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> tuple[NetworkAdapter, str]:
    """Create the configured online adapter and return adapter plus transport label."""
    selected = (transport or os.getenv("CHESSCHAMPION_ONLINE_TRANSPORT", DEFAULT_TRANSPORT)).strip().lower()

    if selected == "tcp":
        tcp_host = (host or os.getenv("CHESSCHAMPION_ONLINE_HOST", DEFAULT_TCP_HOST)).strip()
        raw_port = port if port is not None else os.getenv("CHESSCHAMPION_ONLINE_PORT", str(DEFAULT_TCP_PORT))
        try:
            tcp_port = int(raw_port)
        except (TypeError, ValueError):
            tcp_port = DEFAULT_TCP_PORT

        return TcpJsonNetworkAdapter(tcp_host, tcp_port), f"tcp://{tcp_host}:{tcp_port}"

    if hub is None:
        hub = SessionManagerHub()
    return SessionManagerClientAdapter(hub), "shim://session-manager"
