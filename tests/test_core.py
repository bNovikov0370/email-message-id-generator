# -*- coding: utf-8 -*-
"""Tests for the Email Message ID Generator."""

import re
import unittest
from unittest.mock import patch

from email_message_id_generator import generate_message_id, MessageIdGenerator


# Regex for a valid Message-ID per RFC 5322
# < local-part @ domain >
# local-part can contain dots and alphanumeric plus hyphens
MESSAGE_ID_RE = re.compile(
    r"^<[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}>$"
)


class FakeClock:
    """Deterministic clock for testing."""
    def __init__(self, start: float = 1_000_000.0) -> None:
        self.time = start

    def __call__(self) -> float:
        self.time += 0.001  # 1 millisecond per call
        return self.time


class TestGenerateMessageId(unittest.TestCase):
    def test_returns_string(self):
        msg_id = generate_message_id(domain="test.example.org")
        self.assertIsInstance(msg_id, str)

    def test_format_is_valid(self):
        msg_id = generate_message_id(domain="test.example.org")
        self.assertIsNotNone(MESSAGE_ID_RE.match(msg_id))

    def test_contains_angle_brackets(self):
        msg_id = generate_message_id(domain="test.example.org")
        self.assertTrue(msg_id.startswith("<"))
        self.assertTrue(msg_id.endswith(">"))

    def test_uses_provided_domain(self):
        msg_id = generate_message_id(domain="my.domain.org")
        self.assertIn("@my.domain.org", msg_id)

    def test_invalid_domain_raises(self):
        with self.assertRaises(ValueError):
            generate_message_id(domain="invalid")

    def test_ip_domain_raises(self):
        with self.assertRaises(ValueError):
            generate_message_id(domain="192.168.1.1")

    def test_deterministic_with_fake_clock(self):
        clock = FakeClock()
        id1 = generate_message_id(domain="test.org", clock=clock)
        id2 = generate_message_id(domain="test.org", clock=clock)
        # Timestamps should differ by 1000 microseconds (1 ms)
        # The local parts must be different
        self.assertNotEqual(id1, id2)


class TestMessageIdGenerator(unittest.TestCase):
    def test_generate_returns_string(self):
        gen = MessageIdGenerator(domain="test.example.org")
        msg_id = gen.generate()
        self.assertIsInstance(msg_id, str)

    def test_generate_is_valid_format(self):
        gen = MessageIdGenerator(domain="test.example.org")
        msg_id = gen.generate()
        self.assertIsNotNone(MESSAGE_ID_RE.match(msg_id))

    def test_consecutive_ids_are_unique(self):
        gen = MessageIdGenerator(domain="test.example.org")
        ids = [gen.generate() for _ in range(100)]
        self.assertEqual(len(set(ids)), 100)

    def test_invalid_domain_raises(self):
        gen = MessageIdGenerator(domain="invalid")
        with self.assertRaises(ValueError):
            gen.generate()

    def test_counter_is_monotonic(self):
        # This tests the behavior we actually implemented
        clock = FakeClock()
        gen = MessageIdGenerator(domain="test.org", clock=clock)
        id1 = gen.generate()
        id2 = gen.generate()
        # Extract the counter from the local part
        # Format: <timestamp>.<instance_id>.<counter>.<uuid>@domain
        local1 = id1[1:].split("@")[0]
        local2 = id2[1:].split("@")[0]
        counter1 = int(local1.split(".")[2])
        counter2 = int(local2.split(".")[2])
        self.assertEqual(counter2, counter1 + 1)

    def test_same_clock_different_ids(self):
        # Two generators with the same clock should still produce different IDs
        clock = FakeClock()
        gen1 = MessageIdGenerator(domain="test.org", clock=clock)
        gen2 = MessageIdGenerator(domain="test.org", clock=clock)
        id1 = gen1.generate()
        id2 = gen2.generate()
        self.assertNotEqual(id1, id2)


if __name__ == "__main__":
    unittest.main()
