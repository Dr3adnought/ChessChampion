import os
import unittest

from game.network.bootstrap import create_online_adapter
from game.network.tcp_adapter import TcpJsonNetworkAdapter
from game.network.transport_shim import SessionManagerClientAdapter, SessionManagerHub


class NetworkBootstrapUnitTests(unittest.TestCase):
    def test_create_online_adapter_defaults_to_shim(self):
        adapter, label = create_online_adapter(hub=SessionManagerHub())
        try:
            self.assertIsInstance(adapter, SessionManagerClientAdapter)
            self.assertEqual(label, "shim://session-manager")
        finally:
            adapter.disconnect()

    def test_create_online_adapter_uses_tcp_when_requested(self):
        adapter, label = create_online_adapter(transport="tcp", host="127.0.0.1", port=9001)
        self.assertIsInstance(adapter, TcpJsonNetworkAdapter)
        self.assertEqual(label, "tcp://127.0.0.1:9001")

    def test_create_online_adapter_uses_env_configuration(self):
        previous_transport = os.getenv("CHESSCHAMPION_ONLINE_TRANSPORT")
        previous_host = os.getenv("CHESSCHAMPION_ONLINE_HOST")
        previous_port = os.getenv("CHESSCHAMPION_ONLINE_PORT")

        os.environ["CHESSCHAMPION_ONLINE_TRANSPORT"] = "tcp"
        os.environ["CHESSCHAMPION_ONLINE_HOST"] = "localhost"
        os.environ["CHESSCHAMPION_ONLINE_PORT"] = "9010"

        try:
            adapter, label = create_online_adapter()
            self.assertIsInstance(adapter, TcpJsonNetworkAdapter)
            self.assertEqual(label, "tcp://localhost:9010")
        finally:
            if previous_transport is None:
                os.environ.pop("CHESSCHAMPION_ONLINE_TRANSPORT", None)
            else:
                os.environ["CHESSCHAMPION_ONLINE_TRANSPORT"] = previous_transport

            if previous_host is None:
                os.environ.pop("CHESSCHAMPION_ONLINE_HOST", None)
            else:
                os.environ["CHESSCHAMPION_ONLINE_HOST"] = previous_host

            if previous_port is None:
                os.environ.pop("CHESSCHAMPION_ONLINE_PORT", None)
            else:
                os.environ["CHESSCHAMPION_ONLINE_PORT"] = previous_port


if __name__ == "__main__":
    unittest.main()
