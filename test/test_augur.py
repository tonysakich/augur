#!/usr/bin/env python
"""
augur unit tests.

"""
from __future__ import division
import sys
try:
    import cdecimal
    sys.modules["decimal"] = cdecimal
except:
    pass
import os
import platform
from decimal import Decimal
if platform.python_version() < "2.7":
    unittest = __import__("unittest2")
else:
    import unittest

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(HERE, os.pardir))
sys.path.insert(0, os.path.join(HERE, os.pardir, "augur"))

from ui.app import app, socketio, Api

class TestAugur(unittest.TestCase):

    def setUp(self):
        self.api = Api()
        self.ns = "/socket.io/"
        self.brainwallet = "testmagicbrainwallet"
        self.settings = {
            "host": "localhost",
            "port": 8899,
            "core_path": os.path.join(HERE, "core"),
        }
        self.vote_id = 1
        self.decision_id = 1
        self.state = 0
        app.config["TESTING"] = True
        self.ns = "/socket.io/"
        self.client = socketio.test_client(app, namespace=self.ns)
        self.client.get_received(self.ns)
        # self.socket_emit_receive({
        #     "emit-name": "start",
        # })

    def socket_emit_receive(self, intake):
        label, data = None, None
        emit_name = intake.pop("emit-name", None)
        if intake:
            self.client.emit(emit_name, intake, namespace=self.ns)
        else:
            self.client.emit(emit_name, namespace=self.ns)
        received = self.client.get_received(self.ns)
        if received:
            try:
                label = received[0]["name"]
                data = received[0]["args"][0]
            except:
                label = received[0]["name"]
                data = received[0]["args"]
        return label, data

    def test_settings(self):
        label, data = self.socket_emit_receive({
            "emit-name": "settings",
            "host": self.settings["host"],
            "port": self.settings["port"],
            "core_path": self.settings["core_path"],
        })
        self.assertEqual(label, "settings")
        self.assertIn("host", data)
        self.assertIn("port", data)
        self.assertIn("core_path", data)
        self.assertEqual(data["host"], self.settings["host"])
        self.assertEqual(data["port"], self.settings["port"])
        self.assertEqual(data["core_path"], self.settings["core_path"])

    def test_ping(self):
        label, data = self.socket_emit_receive({
            "emit-name": "ping",
        })
        self.assertIsNotNone(label)
        self.assertIsNotNone(data)

    def test_get_account(self):
        label, data = self.socket_emit_receive({
            "emit-name": "get-account",
        })
        self.assertEqual(label, "account")
        self.assertIn("address", data)
        self.assertIn("privkey", data)
        self.assertIn("cash", data)
        self.assertIn("shares", data)
        self.assertIn("branches", data)
        self.assertIn("decisions", data)

    def test_update_account(self):
        pass
        # label, data = self.socket_emit_receive({
        #     "emit-name": "update-account",
        # })
        # self.assertEqual(label, "account")
        # self.assertIn("cash", data)
        # self.assertIn("shares", data)
        # self.assertIn("branches", data)

    def test_get_block(self):
        label, data = self.socket_emit_receive({
            "emit-name": "get-block",
            "block_number": 1,
        })
        self.assertEqual(label, "block")
        self.assertIsNotNone(data)

    def test_peers(self):
        label, data = self.socket_emit_receive({
            "emit-name": "peers",
        })
        self.assertEqual(label, "peers")
        self.assertIsNotNone(data)

    def test_blockcount(self):
        label, data = self.socket_emit_receive({
            "emit-name": "blockcount",
        })
        self.assertEqual(label, "blockcount")
        self.assertIsNotNone(data)

    def test_report(self):
        self.socket_emit_receive({
            "emit-name": "report",
            "vote_id": self.vote_id,
            "decision_id": self.decision_id,
            "state": self.state,
        })

    def test_explore_block(self):
        label, data = self.socket_emit_receive({
            "emit-name": "explore-block",
            "block_number": 1,
        })
        self.assertEqual(label, "show-block")
        self.assertIsNotNone(data)

    def test_start(self):
        pass
        # self.socket_emit_receive({
        #     "emit-name": "start",
        #     "password": self.brainwallet,
        # })

    def test_stop(self):
        pass
        # self.socket_emit_receive({
        #     "emit-name": "stop",
        # })

    def test_miner(self):
        pass
        # label, data = self.socket_emit_receive({
        #     "emit-name": "miner",
        #     "arg": "start",
        # })
        # self.assertEqual(label, "miner")
        # self.assertEqual(data, "on")

    def test_send_cash(self):
        pass
        # self.socket_emit_receive({
        #     "emit-name": "send-cash",
        #     "amount": 1,
        #     "address": 0,
        # })

    def test_send_reps(self):
        pass
        # self.socket_emit_receive({
        #     "emit-name": "send-cash",
        #     "amount": 1,
        #     "address": 0,
        #     "branch": "random",
        # })

    def test_create_branch(self):
        pass
        # self.socket_emit_receive({
        #     "emit-name": "create-branch",
        #     "name": "potentpotables",
        # })

    def test_add_decision(self):
        pass
        # self.socket_emit_receive({
        #     "emit-name": "add-decision",
        #     "branchId": "random",
        #     "decisionMaturation": 14000,
        #     "decisionId": "somerandomhex",
        #     "decisionText": "Is the cake a lie?",
        # })

    def test_add_market(self):
        pass
        # self.socket_emit_receive({
        #     "emit-name": "add-market",
        #     "decisionId": "7928d7317255e8a7",
        #     "marketInv": 10,
        # })

    def test_update_market(self):
        pass
        # label, data = self.socket_emit_receive({
        #     "emit-name": "update-market",
        #     "id": "6d5ff28910cc0949" + ".market",
        # })
        # self.assertEqual(label, "market")
        # self.assertIsNotNone(data)

    def test_trade(self):
        pass
        # self.socket_emit_receive({
        #     "emit-name": "trade",
        #     "marketId": "1f56c5596200f0f9.market", 
        #     "marketState": "0", 
        #     "tradeAmount": "100", 
        #     "tradeType": "buy",
        # })

    def tearDown(self):
        # self.socket_emit_receive({
        #     "emit-name": "stop",
        # })
        del self.api
        del self.client


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAugur)
    unittest.TextTestRunner(verbosity=2).run(suite)
