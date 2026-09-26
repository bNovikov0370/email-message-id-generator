# -*- coding: utf-8 -*-
"""Core implementation for RFC 5322 Message-ID generation."""

import os
import re
import secrets
import socket
import time
import uuid
from typing import Callable, Optional


__all__ = [
    "generate_message_id",
    "MessageIdGenerator",
]


# Maximum entropy in the random portion of the local part.
# RFC 5322 allows up to 998 octets per line, and the angle brackets
# plus the "@" and the domain consume at least 4 characters.
# 255 keeps us comfortably within limits while providing high entropy.
_MAX_RANDOM_LENGTH = 255


def _is_valid_domain(domain: str) -> bool:
    """Check if a string is a syntactically valid domain name.

    This is a conservative check to ensure the domain part of the
    Message-ID is resolvable and well-formed. It does not guarantee
    the domain exists, but it rejects obviously malformed inputs.
    """
    if not domain or len(domain) > 253:
        return False
    # Reject IP addresses; Message-IDs should use domain names
    if re.match(r"^\[?[0-9a-fA-F:.]+\]?$", domain):
        return False
    # Must contain at least one dot to ensure a fully qualified domain
    if "." not in domain:
        return False
    # Check labels
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    if any(not label for label in labels):
        return False
    for label in labels:
        if len(label) > 63:
            return False
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", label):
            return False
    return True


def _get_default_domain() -> str:
    """Get the default domain for Message-IDs.

    Uses the fully qualified domain name if available, falling back
    to "localhost.localdomain" if the FQDN is not resolvable.
    """
    try:
        fqdn = socket.getfqdn()
        if _is_valid_domain(fqdn):
            return fqdn
    except Exception:
        pass
    return "localhost.localdomain"


def _generate_local_part(length: int = _MAX_RANDOM_LENGTH) -> str:
    """Generate a cryptographically secure random local part.

    Uses `secrets` module for cryptographic security to prevent
    collision attacks. The output is URL-safe base64 encoded to
    ensure RFC 5322 compatibility.
    """
    # Each byte from token_hex becomes 2 characters, so divide length by 2
    num_bytes = (length // 2) + 1
    return secrets.token_hex(num_bytes)[:length]


def generate_message_id(
    domain: Optional[str] = None,
    clock: Callable[[], float] = time.time,
) -> str:
    """Generate a single RFC 5322 compliant Message-ID.

    The Message-ID is constructed as ``<local-part@domain>``. The
    local part combines a timestamp, a UUID, and random bytes to
    ensure global uniqueness even under high concurrency.

    Args:
        domain: The domain to use. If None, the system FQDN is used.
        clock: A callable returning a float timestamp. Injected
            to make tests deterministic. Must be monotonic in
            practice, though not enforced here.

    Returns:
        A string formatted as ``<local-part@domain>``.
    """
    if domain is None:
        domain = _get_default_domain()
    if not _is_valid_domain(domain):
        raise ValueError(f"Invalid domain: {domain}")

    timestamp = int(clock() * 1_000_000)  # microseconds for precision
    unique_uuid = uuid.uuid4().hex
    random_part = _generate_local_part(24)  # 24 chars is plenty

    local_part = f"{timestamp}.{unique_uuid}.{random_part}"

    return f"<{local_part}@{domain}>"


class MessageIdGenerator:
    """Stateful generator for Message-IDs.

    Maintains a monotonic counter to provide additional uniqueness
    guarantees within a process, which is useful for test suites that
    require strictly increasing identifiers.
    """

    def __init__(
        self,
        domain: Optional[str] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        """Initialize the generator.

        Args:
            domain: The domain to use for all generated IDs.
            clock: A callable returning a float timestamp.
        """
        self._domain = domain
        self._clock = clock
        self._counter = 0
        # Mix in OS randomness at init to make instances distinct
        self._instance_id = secrets.token_hex(8)

    def generate(self) -> str:
        """Generate a new unique Message-ID.

        Returns:
            A string formatted as ``<local-part@domain>``.
        """
        if self._domain is None:
            domain = _get_default_domain()
        else:
            domain = self._domain

        if not _is_valid_domain(domain):
            raise ValueError(f"Invalid domain: {domain}")

        timestamp = int(self._clock() * 1_000_000)
        self._counter += 1
        unique_uuid = uuid.uuid4().hex

        local_part = (
            f"{timestamp}.{self._instance_id}."
            f"{self._counter}.{unique_uuid}"
        )

        return f"<{local_part}@{domain}>"
