# -*- coding: utf-8 -*-
"""Email Message ID Generator.

A small, dependency-free library for generating RFC 5322 compliant
Message-ID headers with guaranteed global uniqueness.
"""

from .core import (
    generate_message_id,
    MessageIdGenerator,
)

__all__ = [
    "generate_message_id",
    "MessageIdGenerator",
]
