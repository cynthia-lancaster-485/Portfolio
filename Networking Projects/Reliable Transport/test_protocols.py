"""Stress tests for the Alternating Bit and Go-Back-N implementations.

Each protocol runs in the course's network simulator across many random
seeds and loss/corruption levels. A run passes if the receiver delivers
messages in exactly the order they were sent, nothing crashes, the
simulator reports no invalid calls, and (when the network is not
overloaded) nearly every message gets through.

Run with:  python3 -m unittest test_protocols.py
"""

import contextlib
import importlib
import io
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SEEDS = range(1, 31)
CONDITIONS = [(0.0, 0.0), (0.05, 0.05), (0.1, 0.1)]
NUM_MSGS = 200


def run(module_name, seqnum_limit, seed, loss, corrupt, interarrival):
    """Runs one simulation and returns (messages delivered, simulator output)."""
    sim = importlib.import_module(module_name)
    delivered = []
    options = types.SimpleNamespace(
        num_msgs=NUM_MSGS, interarrival_time=interarrival, seqnum_limit=seqnum_limit,
        loss_prob=loss, corrupt_prob=corrupt, random_seed=seed, trace=0,
    )
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        sim.main(options, None, delivered.append)
    return delivered, output.getvalue()


def expected(count):
    """The simulator sends 'aaaa...', 'bbbb...', and so on, wrapping after 'z'."""
    return [bytes([97 + i % 26]) * 20 for i in range(count)]


class ProtocolStressTest:
    module_name = None
    seqnum_limits = ()
    interarrival = None

    def test_in_order_delivery_under_loss_and_corruption(self):
        for z in self.seqnum_limits:
            for seed in SEEDS:
                for loss, corrupt in CONDITIONS:
                    with self.subTest(seqnum_limit=z, seed=seed, loss=loss, corrupt=corrupt):
                        delivered, output = run(self.module_name, z, seed, loss, corrupt, self.interarrival)
                        self.assertEqual(delivered, expected(len(delivered)))
                        self.assertNotIn("WARNING", output)
                        # Messages still in flight when the simulation stops are not lost.
                        self.assertGreaterEqual(len(delivered), NUM_MSGS - z)


class AlternatingBitTests(ProtocolStressTest, unittest.TestCase):
    module_name = "abp_rdtsim"
    seqnum_limits = (2,)
    interarrival = 100.0


class GoBackNTests(ProtocolStressTest, unittest.TestCase):
    module_name = "gbn_rdtsim"
    seqnum_limits = (4, 8, 16)
    interarrival = 30.0


if __name__ == "__main__":
    unittest.main()
