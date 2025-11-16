"""Queue configuration infrastructure value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QueueConfig:
    """
    Infrastructure configuration for SQS queue.

    This is infrastructure-specific configuration, not a domain concept.
    """

    queue_url: str
    max_concurrent_messages: int = 10
    wait_time_seconds: int = 20
    visibility_timeout: int = 30
    max_number_of_messages: int = 10

    def __post_init__(self):
        """Validate configuration."""
        if not self.queue_url:
            raise ValueError("queue_url cannot be empty")
        if self.max_concurrent_messages < 1:
            raise ValueError("max_concurrent_messages must be positive")
        if self.wait_time_seconds < 0 or self.wait_time_seconds > 20:
            raise ValueError("wait_time_seconds must be between 0 and 20")
