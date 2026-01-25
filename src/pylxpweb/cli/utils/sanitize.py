"""Sanitization utilities for masking sensitive data.

Provides deterministic sanitization that replaces sensitive portions
with realistic-looking characters while preserving format validity.
"""

from __future__ import annotations

import hashlib


def sanitize_serial(serial: str, enabled: bool = True) -> str:
    """Mask serial number with realistic-looking replacement characters.

    Replaces the middle portion of a serial number with deterministic
    pseudo-random alphanumeric characters, keeping the first 2 and last 2
    characters. The replacement is deterministic (same input = same output)
    so sanitized values remain consistent across outputs.

    Args:
        serial: Serial number to sanitize
        enabled: Whether sanitization is enabled (if False, returns unchanged)

    Returns:
        Sanitized serial number like "CE93847560" (if original was "CE12345678")

    Examples:
        >>> sanitize_serial("CE12345678")
        'CE93847560'
        >>> sanitize_serial("CE12345678", enabled=False)
        'CE12345678'
        >>> sanitize_serial("AB")  # Too short
        'AB'
    """
    if not enabled or not serial or len(serial) < 4:
        return serial

    # Keep first 2 and last 2 characters
    prefix = serial[:2]
    suffix = serial[-2:]
    middle_len = len(serial) - 4

    if middle_len <= 0:
        return serial

    # Generate deterministic replacement using hash of original
    # This ensures same serial always produces same sanitized output
    replacement = _generate_replacement(serial, middle_len)

    return f"{prefix}{replacement}{suffix}"


def sanitize_username(username: str, enabled: bool = True) -> str:
    """Mask username while preserving some recognizability.

    Args:
        username: Username/email to sanitize
        enabled: Whether sanitization is enabled

    Returns:
        Sanitized username like "use***er" or "***" if too short
    """
    if not enabled:
        return username
    if not username or len(username) <= 5:
        return "***"
    return f"{username[:3]}***{username[-2:]}"


def _generate_replacement(original: str, length: int) -> str:
    """Generate deterministic replacement characters from original string.

    Uses SHA-256 hash of the original to generate pseudo-random but
    deterministic alphanumeric characters.

    Args:
        original: Original string to derive replacement from
        length: Number of replacement characters needed

    Returns:
        String of alphanumeric replacement characters
    """
    # Characters that look like valid serial number content
    # Mix of uppercase letters and digits
    charset = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # Excluding I, O to avoid confusion

    # Hash the original serial to get deterministic bytes
    hash_bytes = hashlib.sha256(original.encode("utf-8")).digest()

    # Convert hash bytes to replacement characters
    result = []
    for i in range(length):
        # Use modulo to wrap around hash bytes if needed
        byte_idx = i % len(hash_bytes)
        char_idx = hash_bytes[byte_idx] % len(charset)
        result.append(charset[char_idx])

    return "".join(result)
