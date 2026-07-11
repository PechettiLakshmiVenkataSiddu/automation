"""Stable retry classification for worker and adapter failures."""

from __future__ import annotations

from enum import StrEnum


class RetryDisposition(StrEnum):
    RETRY = "retry"
    FAIL = "fail"


def classify_failure(error: Exception) -> RetryDisposition:
    """Only transient transport failures are retried automatically."""
    if isinstance(error, (TimeoutError, ConnectionError)):
        return RetryDisposition.RETRY
    return RetryDisposition.FAIL
