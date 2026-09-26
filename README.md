# Email Message ID Generator

A Python library for generating RFC 5322 compliant `Message-ID` headers with guaranteed global uniqueness using only the standard library.

## Usage

```python
from email_message_id_generator import generate_message_id, MessageIdGenerator

# Generate a single Message-ID
msg_id = generate_message_id(domain="mail.example.org")
print(msg_id)
# Output: <1700000000000000.550e8400e29b.1.7b9f...@mail.example.org>

# Or use the stateful generator for sequential IDs
gen = MessageIdGenerator(domain="mail.example.org")
print(gen.generate())
print(gen.generate())
```

## Why This Library Exists

Generating a Message-ID seems trivial until you need them to be globally unique across distributed processes without coordination. This library combines three sources of uniqueness: a high-resolution timestamp, a UUID4, and cryptographically secure random bytes. The trade-off is that the local parts are longer than minimal, which is acceptable because Message-ID headers are not size-constrained in practice.

## Edge Cases

The domain validation is strict. It rejects IP addresses (e.g., `192.168.1.1`) and single-label hostnames (e.g., `localhost`). If you need to use an IP literal, you must wrap it in brackets yourself, though this library will not generate such IDs. The domain must contain at least one dot and use valid characters only.
